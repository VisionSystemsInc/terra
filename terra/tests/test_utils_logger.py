from unittest import mock
import os

from .utils import TestLoggerConfigureCase, TestSettingsConfigureCase
from terra.utils.logger import log_terra_version
from terra import settings


class TestLogger(TestLoggerConfigureCase, TestSettingsConfigureCase):
  def setUp(self):
    self.config.terra = {'zone': 'controller'}
    super().setUp()

  @mock.patch.dict(os.environ, {'TERRA_BLAH_CWD': "/tmp"})
  @mock.patch('terra.utils.logger.Popen')
  def test_logger_git_call(self, mock_popen):
    # Test normal working case
    communicate = [mock.MagicMock()]
    mock_popen.return_value.communicate.return_value = communicate
    decode = communicate[0].strip.return_value.decode
    decode.return_value = 'blah-2-g7654321'
    with self.assertLogs() as cm:
      log_terra_version(None, None, 'Test App', 'TERRA_BLAH')
    self.assertIn('Terra Test App version: blah-2-g7654321', cm.output[0])

    # Test exception
    decode.side_effect = ValueError('Oh no')
    with self.assertLogs() as cm:
      log_terra_version(None, None, 'Test App', 'TERRA_BLAH')
    self.assertIn('Terra Test App version: Unknown', cm.output[0])

    # Test empty string
    decode.side_effect = None
    decode.return_value = ''
    with self.assertLogs() as cm:
      log_terra_version(None, None, 'Test App', 'TERRA_BLAH')
    self.assertIn('Terra Test App version: Unknown', cm.output[0])

  @mock.patch.dict(os.environ,
                   {'TERRA_BLAH_IMAGE_COMMIT': "blah-2-g1234567",
                    'TERRA_BLAH_DEPLOY_COMMIT': "blah-2-g1234567-dirty"})
  def test_logger(self):
    # The Deploy case, the main controller
    with self.assertLogs() as cm:
      log_terra_version(None, None, 'Test App', 'TERRA_BLAH')
    self.assertIn('Terra Test App Deploy version: blah-2-g1234567-dirty',
                  cm.output[0])

    # The runner should always use the Image commit
    settings.terra.zone = 'runner'
    with self.assertLogs() as cm:
      log_terra_version(None, None, 'Test App', 'TERRA_BLAH')
    self.assertIn('Terra Test App Runner version: blah-2-g1234567',
                  cm.output[0])

    # Other zones should not be spamming the logs
    settings.terra.zone = 'task'
    with self.assertNoLogs() as cm:
      log_terra_version(None, None, 'Test App', 'TERRA_BLAH')


class TestLoggerUnconfiguredSettings(TestLoggerConfigureCase):
  def test_logger(self):
    with self.assertLogs() as cm:
      log_terra_version(None, None, 'Test App', 'TERRA_BLAH')
    self.assertIn('Preconfig - Terra Test App version: Unknown', cm.output[0])
