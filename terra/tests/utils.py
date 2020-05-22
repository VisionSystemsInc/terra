import os
import sys
from unittest import mock

from vsi.test.utils import (
  TestCase as TestCase_original, make_traceback, TestNamedTemporaryFileCase
)

from terra import settings


__all__ = ["TestCase", "make_traceback", "TestNamedTemporaryFileCase",
           "TestSettingsUnconfiguredCase", "TestSettingsConfiguredCase"]


class TestCase(TestCase_original):
  pass


class TestSettingsUnconfiguredCase(TestCase):
  def setUp(self):
    # Useful for tests that set this
    self.patches.append(mock.patch.dict(os.environ,
                                        {'TERRA_SETTINGS_FILE': ""}))
    # Use settings
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    super().setUp()


class TestSettingsConfiguredCase(TestSettingsUnconfiguredCase):
  def setUp(self):
    super().setUp()
    settings.configure({})


class TestLoggerCase(TestCase):
  def setUp(self):
    self.original_system_hook = sys.excepthook
    attrs = {'serve_until_stopped.return_value': True, 'ready': True}
    MockLogRecordSocketReceiver = mock.Mock(**attrs)
    self.patches.append(mock.patch('terra.logger.LogRecordSocketReceiver',
                                   MockLogRecordSocketReceiver))
    super().setUp()

  def tearDown(self):
    sys.excepthook = self.original_system_hook

    super().tearDown()


class TestSignalCase(TestCase):
  def setUp(self):
    self.patches.append(mock.patch.dict(os.environ, TERRA_UNITTEST='0'))
    super().setUp()
