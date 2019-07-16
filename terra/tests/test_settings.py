import os
import json
from unittest import mock
from tempfile import TemporaryDirectory, NamedTemporaryFile
import tempfile

from envcontext import EnvironmentContext

from .utils import TestCase
from terra import settings
from terra.core.exceptions import ImproperlyConfigured
from terra.core.settings import (
  ObjectDict, settings_property, Settings, LazyObject, TerraJSONEncoder
)


class TestLazyObject(TestCase):
  def test_setup(self):
    lazy = LazyObject()

    # Test auto loading
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

  def test_lazy(self):
    lazy = LazyObject()

    self.assertNotIn('values', dir(lazy))
    # Make a dict that can take attribute assignment (aka not built in)
    lazy['_wrapped'] = type("NewDict", (dict,), {})()
    self.assertIn('values', dir(lazy))

    lazy['foo'] = 'bar'
    self.assertEqual(lazy['foo'], 'bar')
    self.assertIn('foo', lazy)

    lazy.test = 15
    self.assertIn('test', dir(lazy))
    self.assertEqual(lazy.test, 15)
    del(lazy.test)
    self.assertFalse(hasattr(lazy, 'test'))

    with self.assertRaises(TypeError):
      del(lazy._wrapped)


class TestObjectDict(TestCase):
  def test_basic(self):
    d = ObjectDict({'foo': 3})
    self.assertEqual(d.foo, 3)
    self.assertEqual(d['foo'], 3)
    with self.assertRaises(AttributeError):
      d.bar

    d['bar'] = 4
    d.far = 5
    self.assertEqual(d.bar, 4)
    self.assertEqual(d['far'], 5)

  def test_corner_cases(self):
    self.assertEqual(ObjectDict({}), {})
    self.assertEqual(ObjectDict(), {})

    with self.assertRaises(TypeError):
      ObjectDict({'a': 1}, {'b': 5})

    a = {'a': 1}
    self.assertEqual(ObjectDict(**a), {'a': 1})

  def test_attributes(self):
    d = ObjectDict()
    d.foo = 3
    self.assertEqual(d.foo, 3)
    d.bar = {'prop': 'value'}
    self.assertEqual(d.bar.prop, 'value')
    self.assertEqual(d, {'foo': 3, 'bar': {'prop': 'value'}})
    d.bar.prop = 'newer'
    self.assertEqual(d.bar.prop, 'newer')

  def test_extraction(self):
    d = ObjectDict({'foo': 0, 'bar': [{'x': 1, 'y': 2}, {'x': 3, 'y': 4}]})

    self.assertTrue(isinstance(d.bar, list))

    self.assertEqual([getattr(x, 'x') for x in d.bar], [1, 3])
    self.assertEqual([getattr(x, 'y') for x in d.bar], [2, 4])

    d = ObjectDict()
    self.assertEqual(list(d.keys()), [])

    d = ObjectDict(foo=3, bar=dict(x=1, y=2))
    self.assertEqual(d.foo, 3)
    self.assertEqual(d.bar.x, 1)

  def test_multiple_lists(self):
    d = ObjectDict({'a': 15, 'b': [[{'c': "foo"}]]})
    self.assertEqual(d.b[0][0].c, 'foo')

  def test_dir(self):
    d = ObjectDict({'a': 15, 'b': [[{'c': "foo"}]]})
    self.assertIn('a', dir(d))
    self.assertIn('b', dir(d))
    self.assertNotIn('c', dir(d))


class TestSettings(TestCase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.patches = []

  def setUp(self):
    self.temp_dir = TemporaryDirectory()
    self.patches.append(mock.patch.dict(os.environ,
                                        {'TERRA_SETTINGS_FILE': ""}))
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    for patch in self.patches:
      patch.start()

  def tearDown(self):
    self.temp_dir.cleanup()
    while self.patches:
      self.patches.pop().stop()
    self.assertFalse('TERRA_SETTINGS_FILE' in os.environ) #TODO: Delete

  def test_lazy_attribute(self):
    with self.assertRaises(ImproperlyConfigured):
      settings.foo

    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15, "b":"22", "c": true}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(repr(settings), '<LazySettings [Unevaluated]>')
    self.assertEqual(settings['a'], 15)
    self.assertTrue(settings.configured)
    self.assertNotEqual(repr(settings), '<LazySettings [Unevaluated]>')

    self.assertEqual(settings['b'], "22")
    self.assertEqual(settings['c'], True)

    self.assertIn('a', dir(settings))
    self.assertIn('b', dir(settings))
    self.assertIn('c', dir(settings))
    self.assertNotIn('22', dir(settings))

  def test_lazy_item(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15, "b":"22", "c": true}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    settings._wrapped = None
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
    with self.assertRaises(AttributeError):
      settings.e
    with self.assertRaises(KeyError):
      settings['e']
    self.assertFalse('e' in settings)
    self.assertFalse('e.t' in settings)
    self.assertFalse('q.z' in settings)
    self.assertTrue('q.x' in settings)
    self.assertTrue('q.foo' in settings)
    self.assertTrue('q.foo.t' in settings)
    self.assertTrue('q' in settings)
    self.assertTrue('a' in settings)
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
    self.assertTrue('e' in settings)
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

    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(settings.a, 12.1)
    self.assertEqual(settings.c.e, 11.1)
    # Verify caching is happening
    self.assertEqual(settings._wrapped.c['e'], 11.1)
    self.assertEqual(settings.c.b, 13.1)
    self.assertEqual(settings.d, d)
    self.assertEqual(settings.d(None), 3)
    with self.assertRaises(AttributeError):
      settings.q
    with self.assertRaises(KeyError):
      settings['q']
    self.assertTrue(settings.configured)

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

  @mock.patch('terra.core.settings.global_templates',
              [({}, {'a': 11, 'b': 22})])
  def test_add_templates(self):
    import terra.core.settings as s
    self.assertEqual(s.global_templates, [({}, {'a': 11, 'b': 22})])
    settings.add_templates([({'a': 11}, {'c': 33})])

    settings.configure()
    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, 22)
    self.assertNotIn("c", settings)

    settings._wrapped = None

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

    with settings:
      self.assertEqual(settings.a, 15)

  @mock.patch('terra.core.settings.global_templates', [])
  def test_json(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15, "b":"22", "c": true}')

    @settings_property
    def c(self):
      return self['a']

    settings.add_templates([({}, {'a': fid.name, 'b_json': fid.name, 'c_json': c})])

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

    settings._wrapped = Settings(
                {'a': 11, 'b': 22, 'q': {'x': c, 'y': c, 'foo': {'t': [c]}}})
    j = json.loads(TerraJSONEncoder.dumps(settings))
    self.assertEqual(j['a'], 11)
    self.assertEqual(j['b'], 22)
    self.assertEqual(j['q']['x'], 33)
    self.assertEqual(j['q']['y'], 33)
    self.assertEqual(j['q']['foo']['t'][0], 33)

  # Test all the properties here
  def test_properties(self):
    settings.configure({})
    with settings:
      settings.processing_dir = '/foobar'
      self.assertEqual(settings.status_file, '/foobar/status.json')

    with self.assertLogs(), settings:
      self.assertEqual(settings.processing_dir, os.getcwd())

    with settings, TemporaryDirectory() as temp_dir:
      settings.config_file = os.path.join(temp_dir, 'foo.bar')
      self.assertEqual(settings.processing_dir, temp_dir)

    def mock_mkdtemp(prefix):
      return f'"{prefix}"'

    with mock.patch.object(tempfile, 'mkdtemp', mock_mkdtemp), \
        self.assertLogs(), settings:
      settings.config_file = '/land/of/foo.bar'
      self.assertEqual(settings.processing_dir, '"terra_"')

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

