from unittest import mock
import os
import sys
from tempfile import NamedTemporaryFile as NamedTemporaryFileOrig
import tempfile

from terra import settings
from .utils import TestCase
from terra import logger
from terra.core import signals


class HandlerLoggingContext(TestCase):
  def test_handler_logging_context(self):
    self.assertTrue(1)
    # set up one memory handler

    # swap with another memoery handler

    # test


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

  def test_temp_file_cleanup(self):
    self.assertExist(self.temp_log_file)
    self.assertFalse(self._logs._configured)
    settings.processing_dir
    self.assertNotExist(self.temp_log_file)
    self.assertTrue(self._logs._configured)

  def test_fail(self):
    self.assertTrue(True)


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
