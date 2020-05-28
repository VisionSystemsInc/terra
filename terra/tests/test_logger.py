from unittest import mock
import io
import os
import sys
import json
import logging
import uuid
import tempfile
import platform
import warnings

from terra.core.exceptions import ImproperlyConfigured
from terra import settings
from .utils import (
  TestCase, make_traceback, TestNamedTemporaryFileCase,
  TestSettingsUnconfiguredCase,
  TestLoggerConfigureCase
)
from terra import logger
from terra.core import signals

# import terra.compute.utils

class TestHandlerLoggingContext(TestCase):
  def test_handler_logging_context(self):
    test_logger = logger.getLogger(f'{__name__}.test_handler_logging_context')
    test_logger.setLevel(logging.INFO)
    handler_default = logging.handlers.MemoryHandler(1000)
    handler_swap = logging.handlers.MemoryHandler(1000)
    test_logger.addHandler(handler_default)

    # Test normal case
    message1 = str(uuid.uuid4())
    test_logger.info(message1)
    self.assertIn(message1, str(handler_default.buffer))

    # The actual test
    message2 = str(uuid.uuid4())
    with logger.HandlerLoggingContext(test_logger, [handler_swap]):
      test_logger.info(message2)

    self.assertNotIn(message2, str(handler_default.buffer))
    self.assertIn(message2, str(handler_swap.buffer))


class TestLogger(TestLoggerConfigureCase):
  pass
  def test_setup_working(self):
    self.assertFalse(settings.configured)
    self.assertEqual(settings.processing_dir, self.temp_dir.name)
    self.assertTrue(settings.configured)

  def test_double_configure(self):
    settings._setup()
    with self.assertLogs():
      with self.assertRaises(ImproperlyConfigured):
        self._logs.configure_logger(None)

  def test_temp_file_cleanup(self):
    tmp_file = self._logs.tmp_file.name
    self.assertExist(tmp_file)
    self.assertFalse(self._logs._configured)
    settings.processing_dir
    self.assertNotExist(tmp_file)
    self.assertTrue(self._logs._configured)

  def test_exception_hook_installed(self):
    self.assertEqual(
        sys.excepthook.__qualname__,
        '_SetupTerraLogger.setup_logging_exception_hook.'
        '<locals>.handle_exception')
    self.assertEqual('terra.logger', sys.excepthook.__module__)

  def test_exception_hook(self):
    def save_exec_info(exc_type, exc, tb):
      self.exc_type = exc_type
      self.exc = exc
      self.tb = tb
    sys.excepthook = save_exec_info
    self._logs.setup_logging_exception_hook()
    with mock.patch('sys.stderr', new_callable=io.StringIO):
      with self.assertLogs() as cm:
        # with self.assertRaises(ZeroDivisionError):
        tb = make_traceback()
        sys.excepthook(ZeroDivisionError,
                      ZeroDivisionError('division by almost zero'), tb)

    self.assertIn('division by almost zero', str(cm.output))
    # Test stack trace stuff in there
    self.assertIn('test_exception_hook', str(cm.output))
    self.assertEqual(self.exc_type, ZeroDivisionError)
    self.assertIsInstance(self.exc, ZeroDivisionError)
    self.assertIs(self.tb, tb)

  def test_root_logger_setup(self):
    self.assertEqual(self._logs.root_logger, logging.getLogger(None))
    self.assertEqual(self._logs.root_logger.level, logger.NOTSET)
    # print(self._logs.root_logger.handlers)

  def test_logs_stderr(self):
    stderr_handler = [h for h in self._logs.root_logger.handlers
                      if hasattr(h, 'stream') and h.stream == sys.stderr][0]
    self.assertEqual(stderr_handler.level, logging.WARNING)
    self.assertIs(self._logs.stderr_handler, stderr_handler)

  def test_logs_temp_file(self):
    temp_handler = [
        h for h in self._logs.root_logger.handlers
        if hasattr(h, 'stream') and h.stream.name == self._logs.tmp_file.name][0]
    # Test that log everything is set
    self.assertEqual(temp_handler.level, logger.NOTSET)
    self.assertEqual(self._logs.root_logger.level, logger.NOTSET)

  def test_formatter(self):
    settings.configure({'processing_dir': self.temp_dir.name,
                        'logging': {'format': 'foo {asctime} {msg}',
                                    'date_format': 'bar',
                                    'style': '{'}})

    # This doesn't get formatted
    # with self.assertLogs(__name__, logger.ERROR) as cm:
    #   logger.getLogger(__name__).error('Hi')

    test_logger = logger.getLogger(f'{__name__}.test_formatter')
    record = logging.LogRecord(__name__, logger.ERROR, __file__, 0, "Hiya", (),
                               None)
    self.assertTrue(test_logger.filter(record))
    self.assertTrue(self._logs.stderr_handler.filter(record))
    self.assertEqual(self._logs.stderr_handler.format(record), "foo bar Hiya")

  def test_hostname(self):
    test_logger = logger.getLogger(f'{__name__}.test_hostname')

    record = test_logger.makeRecord(__name__, logger.ERROR, __file__, 0,
                                    "Hiya", (), None)
    self.assertTrue(test_logger.filter(record))
    self.assertTrue(self._logs.stderr_handler.filter(record))
    self.assertIn(':preconfig)', self._logs.stderr_handler.format(record))

    settings._setup()

    record = test_logger.makeRecord(__name__, logger.ERROR, __file__, 0,
                                    "Hiya", (), None)
    self.assertTrue(test_logger.filter(record))
    self.assertTrue(self._logs.stderr_handler.filter(record))
    self.assertIn(f'({platform.node()}:',
                  self._logs.stderr_handler.format(record))

  # Test https://stackoverflow.com/q/19615876/4166604
  def test_funcName(self):
    stream = io.StringIO()
    test_logger = logger.getLogger(f'{__name__}.test_funcName')
    formatter = logging.Formatter('%(filename)s:%(funcName)s %(msg)s')
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    handler.setLevel(logger.DEBUG2)
    test_logger.addHandler(handler)
    test_logger.setLevel(logger.DEBUG2)

    test_logger.debug2('hiya')
    self.assertEqual(stream.getvalue(),
                     f'{os.path.basename(__file__)}:test_funcName hiya\n')

  def test_funcName_stackinfo(self):
    stream = io.StringIO()
    test_logger = logger.getLogger(f'{__name__}.test_funcName')
    formatter = logging.Formatter('%(filename)s:%(funcName)s %(msg)s')
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    handler.setLevel(logger.DEBUG2)
    test_logger.addHandler(handler)
    test_logger.setLevel(logger.DEBUG2)

    test_logger.debug2('byeee', stack_info=True)
    self.assertNotIn(logger._srcfiles[0], stream.getvalue())
    self.assertNotIn(logger._srcfiles[1], stream.getvalue())
    self.assertIn(
        f'{os.path.basename(__file__)}:test_funcName_stackinfo byeee\n',
        stream.getvalue())

  def test_level(self):
    settings.configure({'processing_dir': self.temp_dir.name,
                        'logging': {'level': 'DEBUG1'}})

    self.assertEqual(settings.logging.level, "DEBUG1")

    self.assertEqual(self._logs.root_logger.level, logger.NOTSET)
    self.assertEqual(self._logs.stderr_handler.level, logger.DEBUG1)

  def test_level_case_insensitive(self):
    with self.assertLogs(level=logger.DEBUG2):
      settings.configure({'processing_dir': self.temp_dir.name,
                          'logging': {'level': 'debug2'}})

    self.assertEqual(settings.logging.level, "debug2")

    self.assertEqual(self._logs.root_logger.level, logger.NOTSET)
    self.assertEqual(self._logs.stderr_handler.level, logger.DEBUG2)

  def test_replay(self):
    # Swap out the stderr stream handler for this test
    test_handler = logging.handlers.MemoryHandler(capacity=1000)
    test_handler.setLevel(
        logger._SetupTerraLogger.default_stderr_handler_level)
    self._logs.root_logger.handlers = [
        test_handler if h is self._logs.stderr_handler
        else h for h in self._logs.root_logger.handlers]
    self._logs.stderr_handler = test_handler

    test_logger = logger.getLogger(f'{__name__}.test_replay')
    message1 = str(uuid.uuid4())
    message2 = str(uuid.uuid4())
    message3 = str(uuid.uuid4())
    test_logger.error(message1)
    test_logger.debug1(message2)
    test_logger.debug2(message3)

    self.assertEqual(str(test_handler.buffer).count(message1), 1)
    self.assertEqual(str(test_handler.buffer).count(message2), 0)
    self.assertEqual(str(test_handler.buffer).count(message3), 0)

    settings.configure({'processing_dir': self.temp_dir.name,
                        'logging': {'level': 'debug1'}})

    self.assertEqual(str(test_handler.buffer).count(message1), 2)
    self.assertEqual(str(test_handler.buffer).count(message2), 1)
    self.assertEqual(str(test_handler.buffer).count(message3), 0)

  def test_configured_file(self):
    settings._setup()
    log_filename = os.path.join(self.temp_dir.name,
                                self._logs.default_log_prefix)

    log_handler = [
        h for h in self._logs.root_logger.handlers
        if hasattr(h, 'stream') and h.stream.name == log_filename][0]

    # Test the defaults
    self.assertEqual(log_handler.level, logger.ERROR)
    self.assertEqual(self._logs.root_logger.level, logger.NOTSET)

  def test_debug1(self):
    message = str(uuid.uuid4())
    with self.assertLogs(level=logger.DEBUG1) as cm:
      logger.getLogger(f'{__name__}.test_debug1').debug1(message)
    self.assertIn(message, str(cm.output))

  def test_debug2(self):
    message = str(uuid.uuid4())
    with self.assertLogs(level=logger.DEBUG2) as cm:
      logger.getLogger(f'{__name__}.test_debug2').debug2(message)
    self.assertIn(message, str(cm.output))

  def test_debug3(self):
    message = str(uuid.uuid4())
    with self.assertLogs(level=logger.DEBUG3) as cm:
      logger.getLogger(f'{__name__}.test_debug3').debug3(message)
    self.assertIn(message, str(cm.output))

  def test_warnings(self):
    message = str(uuid.uuid4())
    with self.assertLogs(level=logger.WARNING) as cm:
      warnings.warn(message)
    self.assertIn(message, str(cm.output))


class TestUnitTests(TestCase):
  def last_test_logger(self):
    import logging
    root_logger = logging.getLogger(None)

    self.assertFalse(
        root_logger.handlers,
        msg="If you are seeing this, one of the other unit tests has "
        "initialized the logger. This side effect should be "
        "prevented for you automatically. If you are seeing this, you "
        "have configured logging manually, and should make sure you "
        "restore it.")
