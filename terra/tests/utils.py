import os
import sys
import json
from unittest import mock

from vsi.test.utils import (
  TestCase, make_traceback, TestNamedTemporaryFileCase
)

from terra import settings


__all__ = ["TestCase", "make_traceback", "TestNamedTemporaryFileCase",
           "TestSettingsUnconfiguredCase", "TestSettingsConfiguredCase",
           "TestComputeCase", "TestExecutorCase", "TestSignalCase",
           "TestLoggerConfigureCase"]


class TestSettingsUnconfiguredCase(TestCase):
  def __init__(self, *args, **kwargs):
    self.settings_filename = ''
    super().__init__(*args, **kwargs)

  def setUp(self):
    # Useful for tests that set this
    self.patches.append(mock.patch.dict(
        os.environ,
        {'TERRA_SETTINGS_FILE': self.settings_filename}))
    # Use settings
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    import terra.core.settings
    self.patches.append(mock.patch.object(terra.core.settings.config_file,
                                          'filename', None))
    super().setUp()


class TestSettingsConfiguredCase(TestSettingsUnconfiguredCase):
  def setUp(self):
    super().setUp()
    settings.configure({})


class TestLoggerCase(TestSettingsUnconfiguredCase, TestNamedTemporaryFileCase):
  def setUp(self):
    self.original_system_hook = sys.excepthook
    attrs = {'serve_until_stopped.return_value': True, 'ready': True}
    MockLogRecordSocketReceiver = mock.Mock(**attrs)
    self.patches.append(mock.patch('terra.logger.LogRecordSocketReceiver',
                                   MockLogRecordSocketReceiver))
    self.patches.append(mock.patch(
        'terra.compute.base.LogRecordSocketReceiver',
        MockLogRecordSocketReceiver))
    # Special customization of TestSettingsUnconfiguredCase
    self.settings_filename = os.path.join(self.temp_dir.name, 'config.json')
    config = {"processing_dir": self.temp_dir.name}
    with open(self.settings_filename, 'w') as fid:
      json.dump(config, fid)

    super().setUp()

    # Run _setup_terra_logger AFTER the patches have been applied, or else the
    # temp files will be in /tmp, not self.temp_dir, and the terra_initial_tmp_
    # files won't get auto cleaned up
    import terra.logger
    self._logs = terra.logger._setup_terra_logger()

  def tearDown(self):
    sys.excepthook = self.original_system_hook

    try:
      self._logs.log_file.close()
    except AttributeError:
      pass
    # Windows is pickier about deleting files
    try:
      if self._logs.tmp_file:
        self._logs.tmp_file.close()
    except AttributeError:
      pass
    self._logs.root_logger.handlers = []
    import terra.core.signals
    terra.core.signals.post_settings_configured.disconnect(
        self._logs.configure_logger)
    terra.core.signals.post_settings_context.disconnect(
        self._logs.reconfigure_logger)
    super().tearDown()


class TestComputeCase(TestCase):
  def setUp(self):
    import terra.compute.utils
    self.patches.append(mock.patch.dict(terra.compute.utils.compute.__dict__))
    super().setUp()


class TestExecutorCase(TestCase):
  def setUp(self):
    import terra.executor.utils
    self.patches.append(mock.patch.dict(
        terra.executor.utils.Executor.__dict__))
    super().setUp()


class TestThreadPoolExecutorCase(TestExecutorCase):
  '''
  Special care is needed for ThreadPoolExecutor because it downcasts settings
  '''

  def setUp(self):
    self.settings_class_patch = mock.patch.object(
        settings, '__class__', type(settings), create=False)
    super().setUp()
    self.settings_class_patch.start()
    # This mock behavior needs to be modified, because setting __class__ is
    # unlike normal attributes, it doesn't get overwritten in __dict__, so
    # setting is_local prevents delattr being called on __class__, which would
    # be the wrong thing to do.
    self.settings_class_patch.is_local = True

    # This class does not mock or clean up __wrapped or __tls, but they do not
    # introduce sideeffects.

  def tearDown(self):
    # This has to be stopped before the rest, or else a setattr error occurs.
    self.settings_class_patch.stop()
    super().tearDown()


class TestSignalCase(TestCase):
  def setUp(self):
    self.patches.append(mock.patch.dict(os.environ, TERRA_UNITTEST='0'))
    super().setUp()


# Enable signals. Most logging tests require configure logger to actually
# be called. LogRecordSocketReceiver is mocked out, so no lasting side
# effects should occur.
class TestLoggerConfigureCase(TestLoggerCase, TestSignalCase,
                              TestComputeCase, TestExecutorCase):
  pass
