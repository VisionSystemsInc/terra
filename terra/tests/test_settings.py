import os
import unittest
from tempfile import TemporaryDirectory
from terra import Settings, LazySettings, settings


class TestSettings(unittest.TestCase):
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

  def test_lazy(self):
    temp_dir = TemporaryDirectory()
    json_file = os.path.join(temp_dir.name, 'config.json')
    os.environ['TERRA_SETTINGS_FILE'] = json_file

    with open(json_file, 'w') as fid:
      fid.write('{"a": 15, "b":"22", "c": true}')

    self.assertEqual(settings._wrapped, None)
    self.assertEqual(settings['a'], 15)
    self.assertNotEqual(settings._wrapped, None)

    settings._wrapped = None
    self.assertEqual(settings.a, 15)
    self.assertNotEqual(settings._wrapped, None)

    self.assertEqual(settings.b, "22")
    self.assertEqual(settings.c, True)

    temp_dir.cleanup()
