import re
import json

from terra.utils.workflow import resumable, AlreadyRunException
from terra import settings
from terra.logger import DEBUG1
from .utils import TestSettingsConfigureCase


class Klass:
  pass


class TestResumable(TestSettingsConfigureCase):

  @staticmethod
  def _getStageName(func):
    return f'{func.__module__}.{func.__qualname__}'

  @staticmethod
  def _setStatus(func_dict, status={}):
    for func, state in func_dict.items():
      func_name = TestResumable._getStageName(func)
      status[func_name] = {'name': func_name, 'state': state}
    with open(settings.status_file, 'w') as fid:
      json.dump(status, fid)
    return status

  def assertStageStatus(self, func, state, status=None):
    if not status:
      with open(settings.status_file, 'r') as fid:
        status = json.load(fid)

    stage_name = self._getStageName(func)
    self.assertIn(stage_name, status)
    self.assertEqual(status[stage_name]['state'], state)

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

  def test_status_file(self):
    @resumable
    def test1(self):
      pass

    test1(Klass())
    self.assertStageStatus(test1, 'done')

  def test_status_file_stop_in_middle(self):
    @resumable
    def test1(self):
      pass

    @resumable
    def test2(self):
      raise RuntimeError('foobar')

    test1(Klass())
    self.assertStageStatus(test1, 'done')

    with self.assertRaisesRegex(RuntimeError, '^foobar$'):
      test2(Klass())
    self.assertStageStatus(test2, 'starting')

  def test_resuming(self):
    @resumable
    def test1(self):
      self.x = 12
      return 11

    @resumable
    def test2(self):
      self.y = 13
      return 17

    klass = Klass()

    with settings:
      settings.resume = True
      self._setStatus({test1: 'done'})

      with self.assertLogs(resumable.__module__, DEBUG1) as cm:
        self.assertIsNone(test1(klass))
        self.assertEqual(test2(klass), 17)

      self.assertEqual(klass.y, 13)
      self.assertFalse(hasattr(klass, 'x'))

      self.assertTrue(any(re.search(
          f"Skipping .*{test1.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Starting stage: .*{test2.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Finished stage: .*{test2.__qualname__}", o) for o in cm.output))

  def test_resuming_after_incomplete(self):
    @resumable
    def test1(self):
      self.x = 12
      return 11

    @resumable
    def test2(self):
      self.y = 13
      return 17

    klass = Klass()

    with settings:
      settings.resume = True
      self._setStatus({test1: 'done', test2: 'starting'})

      with self.assertLogs(resumable.__module__, DEBUG1) as cm:
        self.assertIsNone(test1(klass))
        self.assertEqual(test2(klass), 17)

      self.assertEqual(klass.y, 13)
      self.assertFalse(hasattr(klass, 'x'))

      self.assertTrue(any(re.search(
          f"Skipping .*{test1.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Starting stage: .*{test2.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Finished stage: .*{test2.__qualname__}", o) for o in cm.output))

  def test_resuming_overwrite_when_not_done(self):
    @resumable
    def test1(self):
      self.x = 12
      return settings.overwrite

    @resumable
    def test2(self):
      self.y = 13
      return settings.overwrite

    @resumable
    def test3(self):
      self.z = 14
      return settings.overwrite

    klass = Klass()

    with settings:
      settings.resume = True
      settings.overwrite = False
      self._setStatus({test1: 'done', test2: 'starting'})

      with self.assertLogs(resumable.__module__, DEBUG1) as cm:

        # test1 is done and shouldn't be run
        self.assertIsNone(test1(klass))

        # the stage we resume should have overwrite set to True
        self.assertTrue(test2(klass))

        # the stages following should reset overwrite to what it was before
        self.assertFalse(test3(klass))

      self.assertFalse(hasattr(klass, 'x'))
      self.assertEqual(klass.y, 13)
      self.assertEqual(klass.z, 14)

      self.assertTrue(any(re.search(
          f"Skipping .*{test1.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Starting stage: .*{test2.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Finished stage: .*{test2.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Resuming stage: .*{test2.__qualname__}, "
          "temporarily setting overwrite to True.", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Starting stage: .*{test3.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Finished stage: .*{test3.__qualname__}", o) for o in cm.output))

  def test_resuming_overwrite_when_done(self):
    @resumable
    def test1(self):
      self.x = 12
      return settings.overwrite

    @resumable
    def test2(self):
      self.y = 13
      return settings.overwrite

    @resumable
    def test3(self):
      self.z = 14
      return settings.overwrite

    klass = Klass()

    with settings:
      settings.resume = True
      settings.overwrite = False
      self._setStatus({test1: 'done', test2: 'done'})

      with self.assertLogs(resumable.__module__, DEBUG1) as cm:

        # test1 is done and shouldn't be run
        self.assertIsNone(test1(klass))

        # test2 is done, so it shouldn't be run either
        self.assertIsNone(test2(klass))

        # test3 should run, but overwrite shouldn't be modified
        self.assertFalse(test3(klass))

      self.assertFalse(hasattr(klass, 'x'))
      self.assertFalse(hasattr(klass, 'y'))
      self.assertEqual(klass.z, 14)

      self.assertTrue(any(re.search(
          f"Skipping .*{test1.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Skipping .*{test2.__qualname__}", o) for o in cm.output))
      self.assertFalse(any(re.search(
          f"Resuming stage: .*{test2.__qualname__}, "
          "temporarily setting overwrite to True.", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Starting stage: .*{test3.__qualname__}", o) for o in cm.output))
      self.assertTrue(any(re.search(
          f"Finished stage: .*{test3.__qualname__}", o) for o in cm.output))

  def test_resume_no_status_file(self):
    settings.resume = True

    @resumable
    def test1(self):
      self.x = 12
      return 11

    klass = Klass()

    self.assertNotExist(settings.status_file)
    self.assertEqual(test1(klass), 11)
    self.assertExist(settings.status_file)
    self.assertEqual(klass.x, 12)
