import os
import sys
import json
from unittest import mock

from vsi.test.utils import (
  TestCase, make_traceback, TestNamedTemporaryFileCase
)

from terra import settings
from terra.core.settings import ObjectDict


__all__ = ["TestCase", "make_traceback", "TestNamedTemporaryFileCase",
           "TestSettingsUnconfiguredCase", "TestSettingsConfigureCase",
           "TestComputeCase", "TestExecutorCase", "TestSignalCase",
           "TestLoggerConfigureCase"]


class TestSettingsUnconfiguredCase(TestCase):
  '''
  A Test Case that is ready to allow a terra settings configure for a single
  test case only. It handles the mocking of ``TERRA_SETTINGS_FILE`` and
  ``terra.settings``
  '''

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


class TestSettingsConfigureCase(TestSettingsUnconfiguredCase):
  '''
  Like :class:`TestSettingsUnconfiguredCase`, but configures ``terra.settings``
  using ``self.config`` dictionary for you. ``self.config`` should be modified
  in ``setUp`` before ``super().setUp()`` is called, or anywhere in
  ``__init__``
  '''

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.config = ObjectDict()

  def setUp(self):
    super().setUp()
    if 'processing_dir' not in self.config:
      self.config.processing_dir = self.temp_dir.name
    settings.configure(self.config)


class TestLoggerCase(TestSettingsUnconfiguredCase, TestNamedTemporaryFileCase):
  '''
  A Test Case that allows for configuring the logging for a single test case.
  It handles details like: ``sys.excepthook``,
  ``terra.logger.LogRecordSocketReceiver``, and
  ``terra.compute.base.LogRecordSocketReceiver``. Also sets up a config file
  for ``terra.setting`` to load, and starts the stage 1 setup of logging via
  ``terra.logger._setup_terra_logger``.
  '''

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
  '''
  Test case that mocks for ``_connection`` in
  ``terra.compute.utils.compute``. This allows for a compute to be retrieved
  from the ``ComputeHandler`` for a single test case. More useful when used in
  :class:`TestLoggerConfigureCase`
  '''

  def setUp(self):
    from terra.compute.utils import compute
    self.patches.append(mock.patch.dict(compute.__dict__))
    super().setUp()


class TestExecutorCase(TestCase):
  '''
  Test case for that mocks for ``_connection`` in
  ``terra.executor.utils.Executor``. This allows for an executor to be
  retrieved from the ``ExecutorHandler`` for a single test case. More useful
  when used in :class:`TestLoggerConfigureCase`
  '''

  def setUp(self):
    from terra.executor.utils import Executor
    self.patches.append(mock.patch.dict(Executor.__dict__))
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
  '''
  Disables the ``TERRA_UNITTEST`` environment vairable which stops logging from
  being fully configured and signals from being sent during unit testings.
  :class:`TestLoggerConfigureCase` needs an actual working logger for the
  logging tests.
  '''

  def setUp(self):
    self.patches.append(mock.patch.dict(os.environ, TERRA_UNITTEST='0'))
    super().setUp()


class TestLoggerConfigureCase(TestLoggerCase, TestSignalCase,
                              TestComputeCase, TestExecutorCase):
  '''
  Enable signals and logging. Most logging tests require configure logger to
  actually be called. LogRecordSocketReceiver is mocked out, so no lasting side
  effects should occur.
  '''
  pass
