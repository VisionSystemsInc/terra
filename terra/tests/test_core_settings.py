import os
import sys
import json
import time
import pickle
from unittest import mock
from tempfile import TemporaryDirectory, NamedTemporaryFile
import tempfile

from vsi.vendored.envcontext import EnvironmentContext

from .utils import TestCase, TestLoggerCase, TestLoggerConfigureCase
from terra import settings
from terra import logger
from terra.core.exceptions import ImproperlyConfigured
from terra.core.settings import (
  ObjectDict, settings_property, Settings, LazyObject, TerraJSONEncoder,
  ExpandedString, LazySettings, override_config, json_load
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
      del lazy.test
    with self.assertRaises(NotImplementedError):
      del lazy['test']
    with self.assertRaises(NotImplementedError):
      iter(lazy)
    with self.assertRaises(NotImplementedError):
      len(lazy)

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
    for x, y in zip(iter(lazy), iter(data)):
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
    del lazy.test
    self.assertFalse(hasattr(lazy, 'test'))
    self.assertFalse(hasattr(lazy._wrapped, 'test'))

  def test_lazy_del_attribute_protections(self):
    lazy = LazyObject()
    lazy._wrapped = type("NewDict", (dict,), {})()
    with self.assertRaises(TypeError):
      del lazy._wrapped

  def test_lazy_items(self):
    lazy = LazyObject()
    lazy._wrapped = type("NewDict", (list,), {})((11, 22, 33))

    lazy[1] = 17
    self.assertEqual(lazy[0], 11)
    self.assertEqual(lazy[1], 17)
    self.assertEqual(lazy[2], 33)
    self.assertEqual(len(lazy), 3)
    del lazy[0]
    self.assertEqual(lazy[0], 17)
    self.assertEqual(lazy[1], 33)
    self.assertEqual(len(lazy), 2)

  def test_pickle(self):
    lazy = LazyObject()
    lazy._wrapped = (11, 22, 33)
    s = pickle.dumps(lazy)
    pickled = pickle.loads(s)
    self.assertTupleEqual(pickled._wrapped, lazy._wrapped)
    self.assertIsNot(pickled._wrapped, lazy._wrapped)


class TestObjectDict(TestCase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.cls = ObjectDict

  def test_basic(self):
    d = self.cls({'foo': 3})
    self.assertEqual(d.foo, 3)
    self.assertEqual(d['foo'], 3)

  def test_missing_entry(self):
    d = self.cls()

    with self.assertRaises(KeyError):
      d['bar']

    # This should be attribute, not key error
    with self.assertRaises(AttributeError):
      d.bar

  def test_set_attribute(self):
    d = self.cls()
    d.far = 5
    self.assertEqual(d.far, 5)

  def test_set_index(self):
    d = self.cls()
    d['bar'] = 4
    self.assertEqual(d['bar'], 4)

  def test_cross_setting(self):
    d = self.cls()

    # Set one way
    d['bar'] = 4
    d.far = 5
    # Read the other
    self.assertEqual(d.bar, 4)
    self.assertEqual(d['far'], 5)

  def test_constructor_corner_case(self):
    self.assertEqual(self.cls({}), {})
    self.assertEqual(self.cls(), {})

    with self.assertRaises(TypeError):
      self.cls({'a': 1}, {'b': 5})

  def test_dict_constructor(self):
    a = {'a': 1}
    self.assertEqual(self.cls(**a), a)

  def test_nested_attributes(self):
    d = self.cls()

    # set var to a dict, which should auto convert to self.cls
    d.bar = {'prop': 'value'}
    self.assertIsInstance(d.bar, self.cls)

    # test Reading
    self.assertEqual(d.bar.prop, 'value')

    # test partial setting
    d.bar.prop = 'newer'
    self.assertEqual(d.bar.prop, 'newer')

  def test_comparison(self):
    d = self.cls()
    d.bar = {'prop': 'value'}
    d.foo = 3

    # should compare like a normal dict
    self.assertEqual(d, {'foo': 3, 'bar': {'prop': 'value'}})

  def test_extraction_list(self):
    d = self.cls({'foo': 0, 'bar': [{'x': 1, 'y': 2}, {'x': 3, 'y': 4}]})

    self.assertTrue(isinstance(d.bar, list))

    self.assertEqual([getattr(x, 'x') for x in d.bar], [1, 3])
    self.assertEqual([getattr(x, 'y') for x in d.bar], [2, 4])

  def test_extraction_empty_list(self):
    d = self.cls()
    self.assertEqual(list(d.keys()), [])

  def test_constructor_dict(self):
    d = self.cls(foo=3, bar=dict(x=1, y=2))
    self.assertEqual(d.foo, 3)
    self.assertEqual(d.bar.x, 1)
    self.assertIsInstance(d.bar, self.cls)

  def test_constructor_multiple_lists(self):
    d = self.cls({'a': 15, 'b': [[{'c': "foo"}]]})
    self.assertEqual(d.b[0][0].c, 'foo')
    self.assertIsInstance(d.b[0][0], self.cls)

  def test_dir(self):
    d = self.cls({'a': 15, 'b': [[{'c': "foo"}]]})
    self.assertIn('a', dir(d))
    self.assertIn('b', dir(d))
    self.assertNotIn('c', dir(d))
    self.assertIn('c', dir(d.b[0][0]))

  def test_getattr(self):
    d = self.cls({'a': 3, 'b': {'c': {'d': 'value', 'e': 12}}})
    self.assertEqual(getattr(d, 'a'), 3)
    self.assertEqual(getattr(d, 'b.c.d'), 'value')
    self.assertEqual(getattr(d, 'b.c.e'), 12)
    with self.assertRaises(AttributeError):
      _ = getattr(d, 'b.c.z')

  def test_setattr(self):
    d = self.cls()
    setattr(d, 'a', 3)
    setattr(d, 'b.c.d', 'value')
    setattr(d, 'b.c.e', 12)
    self.assertEqual(d.a, 3)
    self.assertEqual(d.b.c.d, 'value')
    self.assertEqual(d.b.c.e, 12)
    setattr(d, 'b.c.d', 13)
    self.assertEqual(d.b.c.d, 13)

    self.assertDictEqual(d, {'a': 3, 'b': {'c': {'d': 13, 'e': 12}}})

  def test_pop(self):
    d = self.cls({'a': 3, 'b': {'c': {'d': 'value', 'e': 12}}})

    with self.assertRaises(AttributeError):
      _ = d.pop('b.c.z')

    self.assertEqual(d.pop('b.c.e'), 12)
    self.assertNotIn('b.c.e', d)

    self.assertEqual(d.pop('b'), {'c': {'d': 'value'}})
    self.assertNotIn('b', d)

    self.assertDictEqual(d, {'a': 3})

  def test_copyattr(self):
    d = self.cls({'a': 3, 'b': {'c': {'d': 'value', 'e': 12}}})

    d.copyattr('b.c.d', 'b.c.f')
    self.assertEqual(d.b.c.f, 'value')
    self.assertEqual(d.b.c.d, 'value')

    d.b.c.d = 10
    self.assertEqual(d.b.c.f, 'value')
    self.assertEqual(d.b.c.d, 10)

    self.assertDictEqual(
      d, {'a': 3, 'b': {'c': {'d': 10, 'e': 12, 'f': 'value'}}})

  def test_moveattr(self):
    d = self.cls({'a': 3, 'b': {'c': {'d': 'value', 'e': 12}}})

    d.moveattr('b.c.d', 'b.c.f')
    self.assertEqual(d.b.c.f, 'value')
    self.assertNotIn('b.c.d', d)

    self.assertDictEqual(d, {'a': 3, 'b': {'c': {'e': 12, 'f': 'value'}}})


class TestObjectDictSettings(TestObjectDict):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.cls = Settings


class TestSettings(TestLoggerCase):
  # TestLoggerCase sets TERRA_SETTINGS_FILE to a valid file, in order to get
  # an ImproperlyConfigured Exception here, TERRA_SETTINGS_FILE must be set to
  # not a file, such as the empty string.
  @mock.patch.dict(os.environ, TERRA_SETTINGS_FILE='')
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
    settings.configure({"a": 15, "b": "22.3", "c": True})

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

  @mock.patch('terra.core.settings.global_compatibility_settings',
              [('foo', 'a')])
  def test_add_compatibility_settings(self):
    import terra.core.settings as s
    self.assertEqual(s.global_compatibility_settings,
                     [('foo', 'a')])
    settings.add_compatibility_settings([('c.bar', 'c.y')])
    self.assertEqual(s.global_compatibility_settings,
                     [('foo', 'a'), ('c.bar', 'c.y')])

  @mock.patch('terra.core.settings.global_templates',
              [({}, {'a': 11, 'b': {'c': 33, 'd': 44}})])
  @mock.patch('terra.core.settings.global_compatibility_settings',
              [('foo', 'a'), ('b.bar', 'b.c')])
  def test_compatibility_settings(self):

    # input settings
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{ "foo": 55, "b": {"bar": 66, "c": 77} }')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    # not yet configured
    self.assertFalse(settings.configured)

    # capture logs & configure settings
    with self.assertLogs(level='WARNING') as cm, settings:
      pass

    # check logs
    self.assertIn("renaming 'foo' to 'a'", cm.output[0])
    self.assertIn("deleting 'b.bar' as 'b.c'", cm.output[1])

    # check settings
    self.assertTrue(settings.configured)
    self.assertNotIn('foo', settings)
    self.assertNotIn('b.bar', settings)
    self.assertDictEqual(settings.to_dict(),
                         {'a': 55, 'b': {'c': 77, 'd': 44}})

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

  def test_multiple_lazy_contexts(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    with settings:
      settings.b = 12
      self.assertEqual(settings.a, 15)
      self.assertEqual(settings.b, 12)
      with settings:
        settings.a = 16
        settings.c = 27
        self.assertEqual(settings.a, 16)
        self.assertEqual(settings.b, 12)
        self.assertEqual(settings.c, 27)
      self.assertEqual(settings.a, 15)
      self.assertEqual(settings.b, 12)
      self.assertNotIn('c', settings)

    self.assertEqual(settings.a, 15)
    self.assertNotIn('b', settings)
    self.assertNotIn('c', settings)

  def test_json_load(self):
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{}')
    self.assertDictEqual(json_load(fid.name), {})

    # Test an empty file is treated as an empty dict instead of erroring
    self.assertDictEqual(json_load(os.path.devnull), {})

    # Test normal json + comments
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('''{"a": 123, "b": true,
                    "c": "foo bar",
                    "d": {
                      // This is a comment
                      "e": ""
                      /*
                        Also a comment
                      */
                      }
                    }''')
    self.assertDictEqual(json_load(fid.name),
                         {"a": 123,
                          "b": True,
                          "c": "foo bar",
                          "d": {"e": ""}})

    # Erroneous json file
    with NamedTemporaryFile(mode='w', dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a":')
    with self.assertLogs(level=logger.FATAL) as cm:
      with self.assertRaises(SystemExit):
        json_load(fid.name)
    self.assertIn("Error parsing the JSON config file", str(cm.output))

    with self.assertLogs(level=logger.FATAL) as cm:
      with self.assertRaises(SystemExit):
        json_load(os.path.join(self.temp_dir.name, 'does_not_exist.json'))
    self.assertIn("Cannot find JSON config file", str(cm.output))

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
      if os.name == "nt":
        settings.processing_dir = 'C:\\foobar'
        ans = 'C:\\foobar\\status.json'
      else:
        settings.processing_dir = '/foobar'
        ans = '/foobar/status.json'
      self.assertEqual(settings.status_file, ans)

  @mock.patch('os.access')
  def test_properties_processing_dir_default_writable(self, mock_access):
    mock_access.return_value = True   # mock cwd as always writable
    settings.configure({})

    with self.assertLogs(), settings:
      self.assertEqual(settings.processing_dir, os.getcwd())

  @mock.patch('tempfile.mkdtemp')
  @mock.patch('os.access')
  def test_properties_processing_dir_default_nonwritable(self, mock_access,
                                                         mock_mkdtemp):
    mock_access.return_value = False   # mock cwd as never writable
    mock_dir = "/tmp/mock"
    mock_mkdtemp.return_value = mock_dir
    settings.configure({})

    with self.assertLogs(), settings:
      self.assertEqual(settings.processing_dir, mock_dir)

  def test_properties_processing_dir_config_file(self):
    settings.configure({})

    with settings, TemporaryDirectory() as temp_dir:
      settings.terra.config_file = os.path.join(temp_dir, 'foo.bar')
      self.assertEqual(settings.processing_dir, temp_dir)

  def test_properties_processing_dir_nonexisting_config_file(self):
    settings.configure({})

    def mock_mkdtemp(prefix):
      return f'"{prefix}"'

    with mock.patch.object(tempfile, 'mkdtemp', mock_mkdtemp), \
        self.assertLogs(), settings:
      settings.terra.config_file = '/land/of/foo.bar'
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

  def test_expanduser(self):
    settings.configure({'test_dir': '~/foo',
                        'test_that': '~/bar'})

    self.assertEqual(settings.test_dir, os.path.expanduser('~/foo'))
    self.assertNotEqual(settings.test_that, os.path.expanduser('~/bar'))
    self.assertEqual(settings.test_that, '~/bar')

  def test_expanduser_once(self):
    settings.configure({'test_dir': ExpandedString('~/foo'),
                        'test_file': '~/bar'})

    self.assertNotIsInstance(settings._wrapped['test_file'], ExpandedString)
    self.assertEqual(settings.test_file, os.path.expanduser('~/bar'))
    self.assertIsInstance(settings._wrapped['test_file'], ExpandedString)

    self.assertEqual(settings.test_dir, '~/foo')

  def test_expandvars(self):
    with EnvironmentContext(FOO="NOTBAR"):
      settings.configure({'test1': 'this${FOO}that',
                          'test2': 'a${GKLDGSJLGKJSGURNAONV}b'})

    with EnvironmentContext(FOO="BAR"):
      self.assertEqual(settings.test1, 'thisBARthat')
      self.assertEqual(settings.test2, 'a${GKLDGSJLGKJSGURNAONV}b')

  def test_expandvars_once(self):
    settings.configure({'test2': 'a${GKLDGSJLGKJSGURNAONV}b'})

    # Evaluate it here once
    self.assertNotIsInstance(settings._wrapped['test2'], ExpandedString)
    self.assertEqual(settings.test2, 'a${GKLDGSJLGKJSGURNAONV}b')
    self.assertIsInstance(settings._wrapped['test2'], ExpandedString)

    with EnvironmentContext(GKLDGSJLGKJSGURNAONV="FOO"):
      # Show it is not evaluated again here
      self.assertEqual(settings.test2, 'a${GKLDGSJLGKJSGURNAONV}b')

  def test_pickle(self):
    settings.configure({'key': 'value'})
    s = pickle.dumps(settings)
    pickled = pickle.loads(s)
    self.assertDictEqual(pickled._wrapped, settings._wrapped)
    self.assertIsNot(pickled._wrapped, settings._wrapped)

  @mock.patch('terra.core.settings.override_config',
              # Nested
              {"executor": {"num_workers": 12.1,
                            "type": "ThreadPoolExecutor",
                            # Value not set by global templates
                            "foo": "bar",
                            "unset": True},
               # Check top level too
               "resume": "yarp",
               "foo": "bar",
               # Nested that doesn't exist already
               "a": {"b": {"c": 12}}})
  def test_override_config(self):
    # Make sure I include overrides that are setting that both are and aren't
    # specified by the configure command
    settings.configure({"executor": {"type": "DummyExecutor", "foo": "car"},
                        "resume": "nope",
                        "processing_dir": "/foo/bar"})
    self.assertEqual(settings.resume, "yarp")
    self.assertEqual(settings.executor.num_workers, 12.1)
    self.assertEqual(settings.executor.type, "ThreadPoolExecutor")
    self.assertEqual(settings.executor.foo, "bar")
    self.assertEqual(settings.executor.unset, True)
    self.assertEqual(settings.resume, "yarp")
    self.assertEqual(settings.foo, "bar")
    self.assertEqual(settings.processing_dir, "/foo/bar")
    self.assertEqual(settings.compute.arch, "terra.compute.dummy")
    self.assertEqual(settings.a.b.c, 12)


class TestUnitTests(TestCase):
  # Don't make this part of the TestSettings class, it's a TestLoggerCase

  # def test_fail(self):
  #   settings.configure({})

  def last_test_settings(self):
    self.assertIsNone(
        settings._wrapped,
        msg="If you are seeing this, one of the other unit tests has "
            "initialized the settings. This side effect should be "
            "prevented by mocking out the settings._wrapped attribute. "
            "Otherwise unit tests can interfere with each other")

  def last_test_override(self):
    self.assertEqual(
        override_config, {},
        msg="If you are seeing this, one of the other unit tests has "
            "changed the value of override_config. This side effect should be "
            "prevented by mocking out the override_config. Otherwise unit "
            "tests can interfere with each other")


class TestSettingsClass(TestCase):
  def last_test_settings_class(self):
    self.assertEqual(type(settings), LazySettings)


class TestCircularDependency(TestLoggerConfigureCase):
  # I don't want this unloading terra to interfere with other last_tests, as
  # this would reset modules to their initial state, giving false positives to
  # corruption checks. So mock it
  @mock.patch.dict(sys.modules)
  def last_test_import_settings(self):
    # Unload terra
    for module in list(sys.modules.keys()):
      if module.startswith('terra'):
        sys.modules.pop(module)

    import terra.core.settings
    terra.core.settings.settings._setup()

    # Shut down TCP server
    terra.logger._logs.tcp_logging_server.abort = True

    for x in range(1000):
      if not terra.logger._logs.tcp_logging_server.ready:
        break
      time.sleep(0.001)
    else:
      self.assertFalse(terra.logger._logs.tcp_logging_server.ready,
                       'TCP Server did not shut down within a second')

    # Picky windows
    import terra.logger
    terra.logger._logs._log_file.close()
