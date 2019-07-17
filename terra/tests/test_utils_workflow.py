from unittest import mock
import argparse
import os
from tempfile import TemporaryDirectory
import json

from terra.utils.workflow import resumable, AlreadyRunException
from terra import settings
from .utils import TestCase

class Klass:
  pass

class TestResumable(TestCase):
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
    settings.configure({'processing_dir': self.temp_dir.name})

  def tearDown(self):
    self.temp_dir.cleanup()
    while self.patches:
      self.patches.pop().stop()

  def test_simple(self):
    @resumable
    def test1(self):
      self.x = 13
    status = Klass()
    test1(status)
    self.assertEqual(status.x, 13)

  def test_no_multi_run(self):
    @resumable
    def test1(self):
      pass

    test1(Klass())
    with self.assertRaises(AlreadyRunException):
      test1(Klass())
    with self.assertRaises(AlreadyRunException):
      test1(Klass())

  def test_status(self):
    @resumable
    def test1(self):
      pass

    test1(Klass())

    with open(settings.status_file, 'r') as fid:
      status = json.load(fid)
    self.assertEqual(status['stage_status'], 'done')
    self.assertEqual(status['stage'], f'{__file__}//{test1.__qualname__}')

  def test_stop_in_middle(self):
    @resumable
    def test1(self):
      pass

    @resumable
    def test2(self):
      raise RuntimeError('foobar')

    test1(Klass())
    with open(settings.status_file, 'r') as fid:
      status = json.load(fid)
    self.assertEqual(status['stage_status'], 'done')
    self.assertEqual(status['stage'], f'{__file__}//{test1.__qualname__}')

    with self.assertRaisesRegex(RuntimeError, '^foobar$'):
      test2(Klass())

    with open(settings.status_file, 'r') as fid:
      status = json.load(fid)
    self.assertEqual(status['stage_status'], 'starting')
    self.assertEqual(status['stage'], f'{__file__}//{test2.__qualname__}')

  def test_resuming(self):
    @resumable
    def test1(self):
      self.x = 12

    klass = Klass()

    with settings:
      settings.resume = True
      with open(settings.status_file, 'w') as fid:
        json.dump({'stage_status': 'done',
                   'stage':f'{__file__}//{test1.__qualname__}'}, fid)

      print('222')
      test1(klass)
      print('3343')

      self.assertEqual(klass.x, 12)


