import os
from unittest import TestCase, mock
from tempfile import TemporaryDirectory, NamedTemporaryFile
from terra import settings
from terra.core.settings import ObjectDict, setting_property


class TestObjectDict(TestCase):

  def test_basic(self):
    d = ObjectDict({'foo': 3})
    self.assertEqual(d.foo, 3)
    self.assertEqual(d['foo'], 3)
    with self.assertRaises(AttributeError):
      d.bar

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


class TestSettings(TestCase):

  def setUp(self):
    self.temp_dir = TemporaryDirectory()

  def tearDown(self):
    self.temp_dir.cleanup()

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
  @mock.patch('terra.core.settings.global_templates', [({},{'a': 11, 'b': 22, 'q': {'x':33, 'y':44}}), ({'c': {'d': 14}}, {'e':15})])
  def test_global_templates(self):
    with NamedTemporaryFile(mode='w',
                            dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{"b":"333", "c":"444"}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, "333")
    self.assertEqual(settings.c, "444")
    self.assertIsNone(settings.e)
    self.assertFalse('e' in settings)
    self.assertTrue(settings.configured)

  @mock.patch.dict(os.environ, {'TERRA_SETTINGS_FILE': ""})
  @mock.patch.object(settings, '_wrapped', None)
  @mock.patch('terra.core.settings.global_templates', [({},{'a': 11, 'b': 22}), ({'c': {'d': 14}}, {'e': {'f': 15}})])
  def test_global_templates2(self):
    with NamedTemporaryFile(mode='w',
                            dir=self.temp_dir.name,
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

  @mock.patch.dict(os.environ, {'TERRA_SETTINGS_FILE': ""})
  @mock.patch.object(settings, '_wrapped', None)
  @mock.patch('terra.core.settings.global_templates', [({},{})])
  def test_setting_property(self):
    import terra.core.settings
    @setting_property
    def a(self):
      return self.c + 1

    b = lambda self: 13.1

    def c(self):
      return self.b - 2

    def d(self):
      return 3

    terra.core.settings.global_templates[0][1]['a'] = a
    terra.core.settings.global_templates[0][1]['b'] = setting_property(b)
    terra.core.settings.global_templates[0][1]['c'] = setting_property(c)
    terra.core.settings.global_templates[0][1]['d'] = d

    with NamedTemporaryFile(mode='w',
                            dir=self.temp_dir.name,
                            delete=False) as fid:
      fid.write('{}')
    os.environ['TERRA_SETTINGS_FILE'] = fid.name

    self.assertFalse(settings.configured)
    self.assertEqual(settings.a, 12.1)
    self.assertEqual(settings.c, 11.1)
    self.assertEqual(settings.b, 13.1)
    self.assertEqual(settings.d, d)
    self.assertEqual(settings.d(None), 3)
    self.assertTrue(settings.configured)

  @mock.patch.object(settings, '_wrapped', None)
  @mock.patch('terra.core.settings.global_templates', [({},{'a': 11, 'b': 22})])
  def test_configure(self):

    self.assertFalse(settings.configured)
    settings.configure(b="333", c=444)
    self.assertTrue(settings.configured)

    self.assertEqual(settings.a, 11)
    self.assertEqual(settings.b, "333")
    self.assertEqual(settings.c, 444)
