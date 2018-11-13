import os
from unittest import TestCase, mock
from tempfile import TemporaryDirectory, NamedTemporaryFile
from terra import Settings, LazySettings, settings


class TestSettings(TestCase):

  def setUp(self):
    self.temp_dir = TemporaryDirectory()

  def tearDown(self):
    self.temp_dir.cleanup()

  def test_basic(self):
    d = Settings({'foo': 3})
    self.assertEqual(d.foo, 3)
    self.assertEqual(d['foo'], 3)
    with self.assertRaises(AttributeError):
      d.bar

  def test_corner_cases(self):
    self.assertEqual(Settings({}), {})
    self.assertEqual(Settings(None), {})
    self.assertEqual(Settings(), {})

    with self.assertRaises(AssertionError):
      Settings({'a': 1}, {'b': 5})

    a = {'a': 1}
    self.assertEqual(Settings(**a), {'a': 1})

  def test_attributes(self):
    d = Settings()
    d.foo = 3
    self.assertEqual(d.foo, 3)
    d.bar = {'prop': 'value'}
    self.assertEqual(d.bar.prop, 'value')
    self.assertEqual(d, {'foo': 3, 'bar': {'prop': 'value'}})
    d.bar.prop = 'newer'
    self.assertEqual(d.bar.prop, 'newer')

  def test_extraction(self):
    d = Settings({'foo': 0, 'bar': [{'x': 1, 'y': 2}, {'x': 3, 'y': 4}]})

    self.assertTrue(isinstance(d.bar, list))

    self.assertEqual([getattr(x, 'x') for x in d.bar], [1, 3])
    self.assertEqual([getattr(x, 'y') for x in d.bar], [2, 4])

    d = Settings()
    self.assertEqual(list(d.keys()), [])

    d = Settings(foo=3, bar=dict(x=1, y=2))
    self.assertEqual(d.foo, 3)
    self.assertEqual(d.bar.x, 1)

  def test_class(self):
    o = Settings({'clean': True})
    self.assertEqual(list(o.items()), [('clean', True)])

    class Flower(Settings):
      power = 1

    f = Flower()
    self.assertEqual(f.power, 1)

    f = Flower({'height': 12})
    self.assertEqual(f.height, 12)
    self.assertEqual(f['power'], 1)

    self.assertCountEqual(f.keys(), ['height', 'power'])

  @mock.patch.dict(os.environ, {'TERRA_SETTINGS_FILE': ""})
  @mock.patch.object(settings, '_wrapped', None)
  def test_lazy_attribute(self):
    with NamedTemporaryFile(mode='w',
                            dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15, "b":"22", "c": true}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(settings['a'], 15)
    self.assertTrue(settings.configured)

    self.assertEqual(settings['b'], "22")
    self.assertEqual(settings['c'], True)

  @mock.patch.dict(os.environ, {'TERRA_SETTINGS_FILE': ""})
  @mock.patch.object(settings, '_wrapped', None)
  def test_lazy_item(self):
    with NamedTemporaryFile(mode='w',
                            dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"a": 15, "b":"22", "c": true}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    settings._wrapped = None
    self.assertEqual(settings.a, 15)
    self.assertTrue(settings.configured)

    self.assertEqual(settings.b, "22")
    self.assertEqual(settings.c, True)

  @mock.patch.dict(os.environ, {'TERRA_SETTINGS_FILE': ""})
  @mock.patch.object(settings, '_wrapped', None)
  def test_comments(self):
    with NamedTemporaryFile(mode='w',
                            dir=self.temp_dir.name,
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

  @mock.patch.dict(os.environ, {'TERRA_SETTINGS_FILE': ""})
  @mock.patch.object(settings, '_wrapped', None)
  @mock.patch('terra.global_settings', {'a': 11, 'b': 22})
  def test_global_settings(self):
    with NamedTemporaryFile(mode='w',
                            dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"b":"333", "c":"444"}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, "333")
    self.assertEqual(settings.c, "444")
    self.assertTrue(settings.configured)

  @mock.patch.object(settings, '_wrapped', None)
  @mock.patch('terra.global_settings', {'a': 11, 'b': 22})
  def test_configure(self):

    self.assertFalse(settings.configured)
    settings.configure(b="333", c=444)
    self.assertTrue(settings.configured)

    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, "333")
    self.assertEqual(settings.c, 444)
