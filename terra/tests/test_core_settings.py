import os
import sys
import json
from unittest import mock
from tempfile import TemporaryDirectory, NamedTemporaryFile
import tempfile

from envcontext import EnvironmentContext

from .utils import TestCase
from .test_logger import TestLoggerCase

from terra import settings
from terra.core.exceptions import ImproperlyConfigured
from terra.core.settings import (
  ObjectDict, settings_property, Settings, LazyObject, TerraJSONEncoder
)


class TestLazyObject(TestCase):
  def test_setup_called(self):
    lazy = LazyObject()

    # Test auto loading, but since they aren't implemented, the error means
    # _setup is successfully getting called
    with self.assertRaises(NotImplementedError):
      lazy.test
    with self.assertRaises(NotImplementedError):
      lazy['test']
    with self.assertRaises(NotImplementedError):
      lazy.test = 13
    with self.assertRaises(NotImplementedError):
      'test' in lazy
    with self.assertRaises(NotImplementedError):
      lazy['test'] = 12
    with self.assertRaises(NotImplementedError):
      del(lazy.test)
    with self.assertRaises(NotImplementedError):
      del(lazy['test'])
    with self.assertRaises(NotImplementedError):
      iter(lazy)


  def test_lazy_dir(self):
    lazy = LazyObject()

    self.assertNotIn('values', dir(lazy))
    # Make a dict that can take attribute assignment (aka not built in)
    lazy._wrapped = type("NewDict", (dict,), {'quack': 'duck'})()
    # Values is there because _wrapped is a dict
    self.assertIn('values', dir(lazy))
    # quack is there because it's a class level variable
    self.assertIn('quack', dir(lazy))

  def test_lazy_iter(self):
    lazy = LazyObject()
    data = [11, 33, 22]
    lazy._wrapped = data

    # Shrugs
    for x,y in zip(iter(lazy), iter(data)):
      self.assertEqual(x, y)

  def test_lazy_set_item(self):
    lazy = LazyObject()
    lazy._wrapped = type("NewDict", (dict,), {})()

    # set item
    lazy['foo'] = 'bar'
    # verify it is set right
    self.assertEqual(lazy['foo'], 'bar')
    self.assertEqual(lazy._wrapped['foo'], 'bar')

  def test_lazy_contains(self):
    lazy = LazyObject()
    lazy._wrapped = type("NewDict", (dict,), {})(foo='bar')

    self.assertIn('foo', lazy)

  def test_lazy_set_attribute(self):
    lazy = LazyObject()
    lazy._wrapped = type("NewDict", (dict,), {})()

    lazy.test = 15
    with self.assertRaises(AttributeError):
      object.__getattribute__(lazy, 'test')
    self.assertEqual(object.__getattribute__(lazy._wrapped, 'test'), 15)
    self.assertIn('test', dir(lazy))

  def test_lazy_del_attribute(self):
    lazy = LazyObject()
    lazy._wrapped = type("NewDict", (dict,), {})()

    lazy.test = 17
    self.assertTrue(hasattr(lazy, 'test'))
    self.assertTrue(hasattr(lazy._wrapped, 'test'))
    del(lazy.test)
    self.assertFalse(hasattr(lazy, 'test'))
    self.assertFalse(hasattr(lazy._wrapped, 'test'))

  def test_lazy_del_attribute_protections(self):
    lazy = LazyObject()
    lazy._wrapped = type("NewDict", (dict,), {})()
    with self.assertRaises(TypeError):
      del(lazy._wrapped)


class TestObjectDict(TestCase):
  def test_basic(self):
    d = ObjectDict({'foo': 3})
    self.assertEqual(d.foo, 3)
    self.assertEqual(d['foo'], 3)

  def test_missing_entry(self):
    d = ObjectDict()

    with self.assertRaises(KeyError):
      d['bar']

    # This should be attribute, not key error
    with self.assertRaises(AttributeError):
      d.bar

  def test_set_attribute(self):
    d = ObjectDict()
    d.far = 5
    self.assertEqual(d.far, 5)

  def test_set_index(self):
    d = ObjectDict()
    d['bar'] = 4
    self.assertEqual(d['bar'], 4)

  def test_cross_setting(self):
    d = ObjectDict()

    # Set one way
    d['bar'] = 4
    d.far = 5
    # Read the other
    self.assertEqual(d.bar, 4)
    self.assertEqual(d['far'], 5)

  def test_constructor_corner_case(self):
    self.assertEqual(ObjectDict({}), {})
    self.assertEqual(ObjectDict(), {})

    with self.assertRaises(TypeError):
      ObjectDict({'a': 1}, {'b': 5})

  def test_dict_constructor(self):
    a = {'a': 1}
    self.assertEqual(ObjectDict(**a), a)

  def test_nested_attributes(self):
    d = ObjectDict()

    # set var to a dict, which should auto convert to ObjectDict
    d.bar = {'prop': 'value'}
    self.assertIsInstance(d.bar, ObjectDict)

    # test Reading
    self.assertEqual(d.bar.prop, 'value')


    # test partial setting
    d.bar.prop = 'newer'
    self.assertEqual(d.bar.prop, 'newer')

  def test_comparison(self):
    d = ObjectDict()
    d.bar = {'prop': 'value'}
    d.foo = 3

    # should compare like a normal dict
    self.assertEqual(d, {'foo': 3, 'bar': {'prop': 'value'}})

  def test_extraction_list(self):
    d = ObjectDict({'foo': 0, 'bar': [{'x': 1, 'y': 2}, {'x': 3, 'y': 4}]})

    self.assertTrue(isinstance(d.bar, list))

    self.assertEqual([getattr(x, 'x') for x in d.bar], [1, 3])
    self.assertEqual([getattr(x, 'y') for x in d.bar], [2, 4])

  def test_extraction_empty_list(self):
    d = ObjectDict()
    self.assertEqual(list(d.keys()), [])

  def test_constructor_dict(self):
    d = ObjectDict(foo=3, bar=dict(x=1, y=2))
    self.assertEqual(d.foo, 3)
    self.assertEqual(d.bar.x, 1)
    self.assertIsInstance(d.bar, ObjectDict)

  def test_constructor_multiple_lists(self):
    d = ObjectDict({'a': 15, 'b': [[{'c': "foo"}]]})
    self.assertEqual(d.b[0][0].c, 'foo')
    self.assertIsInstance(d.b[0][0], ObjectDict)

  def test_dir(self):
    d = ObjectDict({'a': 15, 'b': [[{'c': "foo"}]]})
    self.assertIn('a', dir(d))
    self.assertIn('b', dir(d))
    self.assertNotIn('c', dir(d))
    self.assertIn('c', dir(d.b[0][0]))


class TestSettings(TestCase):
  def setUp(self):
    # Useful for tests that set this
    self.patches.append(mock.patch.dict(os.environ,
                                        {'TERRA_SETTINGS_FILE': ""}))
    # Use settings
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    super().setUp()

  def test_unconfigured(self):
    with self.assertRaises(ImproperlyConfigured):
      settings.foo

  def test_settings_file(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15, "b":"22.3", "c": true}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(repr(settings), '<LazySettings [Unevaluated]>')
    # int
    self.assertEqual(settings['a'], 15)
    self.assertTrue(settings.configured)
    self.assertNotEqual(repr(settings), '<LazySettings [Unevaluated]>')

    # str
    self.assertEqual(settings['b'], "22.3")
    self.assertNotIn('22.3', dir(settings))
    # bool
    self.assertEqual(settings['c'], True)

  def test_lazy_dir(self):
    settings.configure({"a": 15, "b":"22.3", "c": True})

    self.assertIn('a', dir(settings))
    self.assertIn('b', dir(settings))
    self.assertIn('c', dir(settings))

  def test_settings_file_item(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15, "b":"22", "c": true}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(settings.a, 15)
    self.assertTrue(settings.configured)

    self.assertEqual(settings.b, "22")
    self.assertEqual(settings.c, True)

  def test_comments(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{\n'
                '  "a": 15,\n'
                '\n'
                '  // b needs to be a string\n'
                '  "b":"22",\n'
                '  "c": true\n'
                '}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(settings.a, 15)
    self.assertTrue(settings.configured)
    self.assertEqual(settings.b, "22")
    self.assertEqual(settings.c, True)

  def test_nested_in(self):
    settings.configure({'a': 11, 'b': 22, 'q': {'x': 33, 'y': 44,
                                                'foo': {'t': 15}}})
    self.assertIn('a', settings)
    self.assertIn('b', settings)
    self.assertIn('q', settings)
    self.assertNotIn('x', settings)
    self.assertNotIn('y', settings)
    self.assertNotIn('foo', settings)
    self.assertNotIn('t', settings)
    self.assertIn('q.x', settings)
    self.assertIn('q.y', settings)
    self.assertIn('q.foo', settings)
    self.assertNotIn('q.t', settings)
    self.assertIn('q.foo.t', settings)


  @mock.patch('terra.core.settings.global_templates',
              [({},
                {'a': 11, 'b': 22, 'q': {'x': 33, 'y': 44, 'foo': {'t': 15}}}),
               ({'c': {'d': 14}},
                {'e': 15})])
  def test_global_templates(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"b":"333", "c":"444"}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, "333")
    self.assertEqual(settings.c, "444")
    self.assertEqual(settings.q, {'x': 33, 'y': 44, 'foo': {'t': 15}})
    self.assertTrue(settings.configured)

  @mock.patch('terra.core.settings.global_templates',
              [({}, {'a': 11, 'b': 22}), ({'c': {'d': 14}}, {'e': {'f': 15}})])
  def test_global_templates2(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"c": {"d": 14}}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, 22)
    self.assertEqual(settings.c.d, 14)
    self.assertEqual(settings.e.f, 15)
    self.assertTrue(settings.configured)

  @mock.patch('terra.core.settings.global_templates', [({}, {})])
  def test_settings_property(self):
    import terra.core.settings

    @settings_property
    def a(self):
      return self.c.e + 1

    def ce(self):
      return self.c.b - 2

    def d(self):
      return 3

    terra.core.settings.global_templates[0][1].update({
        'a': a,
        'c': {
            'e': settings_property(ce),
            'b': settings_property(lambda self: 13.1),
        },
        'd': d
    })

    self.assertFalse(settings.configured)
    settings.configure()

    # Not cached
    self.assertNotEqual(settings._wrapped['a'], 12.1)
    self.assertEqual(settings.a, 12.1)
    # Verify cached
    self.assertEqual(settings._wrapped['a'], 12.1)

    self.assertEqual(settings.c.e, 11.1)
    self.assertEqual(settings.c.b, 13.1)

    # A non settings_property function is just a function
    self.assertEqual(settings.d, d)
    self.assertEqual(settings.d(None), 3)

  @mock.patch('terra.core.settings.global_templates',
              [({}, {'a': 11, 'b': 22})])
  def test_configure(self):

    self.assertFalse(settings.configured)
    settings.configure(b="333", c=444)
    with self.assertRaises(ImproperlyConfigured):
      settings.configure()
    self.assertTrue(settings.configured)

    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, "333")
    self.assertEqual(settings.c, 444)

  def test_undefined_key(self):
    settings.configure()

    with self.assertRaises(AttributeError):
      settings.q
    with self.assertRaises(KeyError):
      settings['q']
    self.assertTrue(settings.configured)

  @mock.patch('terra.core.settings.global_templates',
              [({}, {'a': 11, 'b': 22})])
  def test_add_templates_domino(self):
    import terra.core.settings as s
    self.assertEqual(s.global_templates, [({}, {'a': 11, 'b': 22})])
    settings.add_templates([({'a': 11}, {'c': 33})])

    settings.configure()
    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, 22)
    self.assertNotIn("c", settings)

  @mock.patch('terra.core.settings.global_templates',
              [({}, {'a': 11, 'b': 22})])
  def test_add_templates_order(self):
    import terra.core.settings as s

    settings.add_templates([({'a': 11}, {'c': 33})])
    # Demonstrate one of the possible complications/solutions.
    settings.add_templates([({}, {'a': 11})])
    self.assertEqual(s.global_templates, [({}, {'a': 11}),
                                          ({'a': 11}, {'c': 33}),
                                          ({}, {'a': 11, 'b': 22})])
    settings.configure()
    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, 22)
    self.assertIn("c", settings)
    self.assertEqual(settings.c, 33)

  def test_with_context(self):
    settings._wrapped = Settings({'a': 11, 'b': 22})
    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, 22)
    self.assertFalse(hasattr(settings, 'c'))

    with settings:
      settings.a = 12
      settings.c = 3
      self.assertEqual(settings.a, 12)
      self.assertEqual(settings.b, 22)
      self.assertEqual(settings.c, 3)

    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, 22)
    self.assertFalse(hasattr(settings, 'c'))

  def test_lazy_context(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    with settings:
      settings.b = 12
      self.assertEqual(settings.a, 15)
      self.assertEqual(settings.b, 12)

    self.assertEqual(settings.a, 15)
    self.assertNotIn('b', settings)

  @mock.patch('terra.core.settings.global_templates', [])
  def test_json(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15, "b":"22", "c": true}')

    @settings_property
    def c(self):
      return self['a']

    settings.add_templates([({},
                             {'a': fid.name,
                              'b_json': fid.name,
                              # Both json AND settings_property
                              'c_json': c})])

    settings.configure({})

    self.assertEqual(settings.a, fid.name)
    self.assertEqual(settings.b_json.a, 15)
    self.assertEqual(settings.b_json.b, "22")
    self.assertEqual(settings.b_json.c, True)
    self.assertEqual(settings.c_json.a, 15)
    self.assertEqual(settings.c_json.b, "22")
    self.assertEqual(settings.c_json.c, True)

  def test_json_serializer(self):

    @settings_property
    def c(self):
      return self.a + self.b

    with self.assertRaises(ImproperlyConfigured):
      TerraJSONEncoder.dumps(settings)

    settings._wrapped = Settings({'a': 11, 'b': 22, 'c': c})
    j = json.loads(TerraJSONEncoder.dumps(settings))
    self.assertEqual(j['a'], 11)
    self.assertEqual(j['b'], 22)
    self.assertEqual(j['c'], 33)

  def test_nested_json_serializer(self):
    @settings_property
    def c(self):
      return self.a + self.b

    settings._wrapped = Settings(
                {'a': 11, 'b': 22, 'q': {'x': c, 'y': c, 'foo': {'t': [c]}}})
    j = json.loads(TerraJSONEncoder.dumps(settings))
    self.assertEqual(j['a'], 11)
    self.assertEqual(j['b'], 22)
    self.assertEqual(j['q']['x'], 33)
    self.assertEqual(j['q']['y'], 33)
    self.assertEqual(j['q']['foo']['t'][0], 33)

  def test_properties_status_file(self):
    settings.configure({})
    with settings:
      settings.processing_dir = '/foobar'
      self.assertEqual(settings.status_file, '/foobar/status.json')

  def test_properties_processing_dir_default(self):
    settings.configure({})

    with self.assertLogs(), settings:
      self.assertEqual(settings.processing_dir, os.getcwd())

  def test_properties_status_file(self):
    settings.configure({})

    with settings, TemporaryDirectory() as temp_dir:
      settings.config_file = os.path.join(temp_dir, 'foo.bar')
      self.assertEqual(settings.processing_dir, temp_dir)

  def test_properties_processing_dir_config_file(self):
    settings.configure({})

    def mock_mkdtemp(prefix):
      return f'"{prefix}"'

    with mock.patch.object(tempfile, 'mkdtemp', mock_mkdtemp), \
        self.assertLogs(), settings:
      settings.config_file = '/land/of/foo.bar'
      self.assertEqual(settings.processing_dir, '"terra_"')

  def test_properties_unittest(self):
    settings.configure({})

    with settings, EnvironmentContext(TERRA_UNITTEST="1"):
      self.assertTrue(settings.unittest)

    with settings, EnvironmentContext(TERRA_UNITTEST="0"):
      self.assertFalse(settings.unittest)

    # Test when unset
    with settings, EnvironmentContext(TERRA_UNITTEST='1'):
      os.environ.pop('TERRA_UNITTEST')
      self.assertFalse(settings.unittest)

    # Make sure I didn't break anything
    self.assertEqual(os.environ['TERRA_UNITTEST'], '1')


class TestUnitTests(TestCase):
  # Don't make this part of the TestSettings class

  # def test_fail(self):
  #   settings.configure({})

  def last_test_settings(self):
    self.assertIsNone(
        settings._wrapped,
        msg="If you are seting this, one of the other unit tests has "
            "initialized the settings. This side effect should be "
            "prevented by mocking out the settings._wrapped attribute. "
            "Otherwise unit tests can interfere with each other")


class TestCircularDependency(TestLoggerCase):
  # I don't want this unloading terra to interfere with other last_tests, as
  # this would reset modules to their initial state, giving false positives to
  # corruption checks. So mock it
  @mock.patch.dict(sys.modules)
  @mock.patch.dict(os.environ, TERRA_UNITTEST='0')  # Needed to make circular
  def last_test_import_settings(self):
    # Unload terra
    for module in list(sys.modules.keys()):
      if module.startswith('terra'):
        sys.modules.pop(module)

    import terra.core.settings
    terra.core.settings.settings._setup()
