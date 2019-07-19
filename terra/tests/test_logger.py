from unittest import mock
import os
import sys
from tempfile import NamedTemporaryFile as NamedTemporaryFileOrig
import logging
import uuid
import tempfile
import platform

from terra.core.exceptions import ImproperlyConfigured
from terra import settings
from .utils import TestCase, make_traceback
from terra import logger
from terra.core import signals


class TestHandlerLoggingContext(TestCase):
  def test_handler_logging_context(self):
    test_logger = logger.getLogger(f'{__name__}.test_handler_logging_context')
    test_logger.setLevel(logging.INFO)
    handler_default = logging.handlers.MemoryHandler(1000)
    handler_swap = logging.handlers.MemoryHandler(1000)
    test_logger.logger.addHandler(handler_default)

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

def NamedTemporaryFileFactory(test_self):
  def NamedTemporaryFile(**kwargs):
    kwargs['dir'] = test_self.temp_dir.name
    rv = NamedTemporaryFileOrig(**kwargs)
    test_self.temp_log_file = rv.name
    return rv
  return NamedTemporaryFile

class TestLogger(TestCase):
  def setUp(self):
    self.original_system_hook = sys.excepthook
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    self.patches.append(mock.patch.object(tempfile, 'NamedTemporaryFile',
                                          NamedTemporaryFileFactory(self)))
    settings_filename = os.path.join(self.temp_dir.name, 'config.json')
    self.patches.append(mock.patch.dict(os.environ,
                                        TERRA_SETTINGS_FILE=settings_filename))
    super().setUp()

    # Don't use settings.configure here, because I need to test out logging
    # signals
    with open(settings_filename, 'w') as fid:
      fid.write(f'{{"processing_dir": "{self.temp_dir.name}"}}')

    self._logs = logger._SetupTerraLogger()

    # # register post_configure with settings
    signals.post_settings_configured.connect(self._logs.configure_logger)

  def tearDown(self):
    # Remove all the logger handlers
    sys.excepthook = self.original_system_hook
    try:
      self._logs.log_file.close()
    except AttributeError:
      pass
    self._logs.root_logger.handlers = []
    signals.post_settings_configured.disconnect(self._logs.configure_logger)
    # Apparently this is unnecessary because signals use weak refs, that are
    # auto removed on free, but I think it's still better to put this here.
    super().tearDown()

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
    self.assertExist(self.temp_log_file)
    self.assertFalse(self._logs._configured)
    settings.processing_dir
    self.assertNotExist(self.temp_log_file)
    self.assertTrue(self._logs._configured)

  def test_exception_hook_installed(self):
    self.assertEqual(sys.excepthook.__qualname__,
        '_SetupTerraLogger.setup_logging_exception_hook.'
        '<locals>.handle_exception')
    self.assertEqual('terra.logger', sys.excepthook.__module__)

  def test_exception_hook(self):
    def save_exec_info(exc_type, exc, tb):
      save_exec_info.exc_type = exc_type
      save_exec_info.exc = exc
      save_exec_info.tb = tb
    sys.excepthook = save_exec_info
    self._logs.setup_logging_exception_hook()
    with self.assertLogs() as cm:
      # with self.assertRaises(ZeroDivisionError):
        tb = make_traceback()
        sys.excepthook(ZeroDivisionError, ZeroDivisionError('division by almost zero'), tb)

    self.assertIn('division by almost zero', str(cm.output))
    # Test stack trace stuff in there
    self.assertIn('test_exception_hook', str(cm.output))
    self.assertEqual(save_exec_info.exc_type, ZeroDivisionError)
    self.assertIsInstance(save_exec_info.exc, ZeroDivisionError)
    self.assertIs(save_exec_info.tb, tb)

  def test_root_logger_setup(self):
    self.assertEqual(self._logs.root_logger, logging.getLogger(None))
    self.assertEqual(self._logs.root_logger.level, logger.NOTSET)
    # print(self._logs.root_logger.handlers)

  def test_logs_stderr(self):
    stderr_handler = [h for h in self._logs.root_logger.handlers
                      if hasattr(h, 'stream') and h.stream == sys.stderr][0]
    self.assertIs(self._logs.stderr_handler, stderr_handler)
    self.assertEqual(stderr_handler.level, logging.WARNING)

  def test_logs_temp_file(self):
    temp_handler = [h for h in self._logs.root_logger.handlers
        if hasattr(h, 'stream') and h.stream.name == self.temp_log_file][0]
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
    record = logging.LogRecord(__name__, logger.ERROR, __file__, 0, "Hiya", (),
                               None)
    self.assertEqual(self._logs.stderr_handler.format(record), "foo bar Hiya")

  # def test_hostname(self):
  #   # settings.configure({'processing_dir': self.temp_dir.name,
  #   #                     'logging': {'format': 'foo {asctime} {msg}'}})

  #   record = logging.LogRecord(__name__, logger.ERROR, __file__, 0, "Hiya", (),
  #                              None)
  #   self.assertIn('(preconfig)', self._logs.stderr_handler.format(record))

  #   settings._setup()

  #   test_logger = logger.getLogger(f'{__name__}.test_hostname')

  #   record = logging.LogRecord(__name__, logger.ERROR, __file__, 0, "Hiya", (),
  #                              None, extra=test_logger.extra)
  #   self.assertIn(f'({platform.node()})', self._logs.stderr_handler.format(record))


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
    self._logs.root_logger.handlers = [
        test_handler if h is self._logs.stderr_handler
        else h for h in self._logs.root_logger.handlers]
    self._logs.stderr_handler = test_handler


    test_logger = logger.getLogger(f'{__name__}.test_replay')
    test_logger.error('hi')
    settings._setup()

  def test_configured_file(self):
    settings._setup()
    log_filename = os.path.join(self.temp_dir.name,
                                self._logs.default_log_prefix)

    log_handler = [h for h in self._logs.root_logger.handlers
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

class TestUnitTests(TestCase):
  def last_test_logger(self):
    import logging
    root_logger = logging.getLogger(None)

    self.assertFalse(root_logger.handlers,
        msg="If you are seting this, one of the other unit tests has "
            "initialized the logger. This side effect should be "
            "prevented for you automatically. If you are seeing this, you "
            "have configured logging manually, and should make sure you "
            "restore it.")
