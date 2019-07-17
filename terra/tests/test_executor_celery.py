import sys
import os
from unittest import mock, skipUnless

try:
  import celery
except:
  celery = None

from terra import settings
from .utils import TestCase


@skipUnless(celery, "Celery not installed")
class TestCeleryConfig(TestCase):
  def setUp(self):
    self.patches.append(mock.patch.dict(os.environ,
                                        TERRA_CWD=self.temp_dir.name))
    self.patches.append(mock.patch.dict(os.environ,
                                        TERRA_REDIS_SECRET_FILE='foo'))
    with open(os.path.join(self.temp_dir.name, 'foo'), 'w') as fid:
      fid.write('hiya')
    super().setUp()

  def tearDown(self):
    super().tearDown()

    if 'terra.executor.celery.celeryconfig' in sys.modules:
      sys.modules.pop('terra.executor.celery.celeryconfig')

  def test_no_redis_passwordfile(self):
    os.remove(os.path.join(self.temp_dir.name, 'foo'))
    with self.assertRaises(FileNotFoundError), self.assertLogs():
      import terra.executor.celery.celeryconfig

  def test_redis_passwordfile(self):
    import terra.executor.celery.celeryconfig as cc
    self.assertEqual(cc.password, 'hiya')

  @mock.patch.dict(os.environ, TERRA_CELERY_INCLUDE='["foo", "bar"]')
  def test_include(self):
    import terra.executor.celery.celeryconfig as cc
    self.assertEqual(cc.include, ['foo', 'bar'])


@skipUnless(celery, "Celery not installed")
class TestSomething(TestCase):
  def setUp(self):
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    super().setUp()
    settings.configure({})

  def test_something(self):
    self.assertTrue(1)
