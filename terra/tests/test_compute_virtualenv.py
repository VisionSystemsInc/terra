import os
from unittest import mock

from terra import settings
from terra.executor.utils import Executor
from terra.compute import base
from terra.compute import virtualenv
import terra.compute.utils

from .utils import TestSettingsConfigureCase


class MockVirtualEnvService(virtualenv.Service):
  def __init__(self):
    super().__init__()
    self.command = ["ls"]
    self.env["BAR"] = "FOO"


class TestVirtualEnv(TestSettingsConfigureCase):
  def setUp(self):
    # self.run trigger Executor
    self.patches.append(mock.patch.dict(Executor.__dict__))
    # This will resets the _connection to an uninitialized state
    self.patches.append(
        mock.patch.object(
            terra.compute.utils.ComputeHandler,
            '_connection',
            mock.PropertyMock(return_value=virtualenv.Compute())))

    # Use mock_popen to check the arguments
    self.patches.append(mock.patch.object(virtualenv,
                                          'Popen', self.mock_popen))

    # patches.append(mock.patch.dict(base.services, clear=True))
    self.config.compute = {'arch': 'virtualenv', 'virtualenv_dir': None}
    super().setUp()

  # Store args, and return an object with a wait call
  def mock_popen(_self, *args, **kwargs):
    _self.popen_args = args
    _self.popen_kwargs = kwargs

    class MockJust:
      def wait(self):
        return _self.return_value

      @property
      def returncode(self):
        return _self.return_value
    return MockJust()

  def test_run_failed(self):
    compute = virtualenv.Compute()
    service = MockVirtualEnvService()

    self.return_value = 1

    import warnings
    with warnings.catch_warnings():
      with self.assertRaises(base.ServiceRunFailed):
        warnings.simplefilter('ignore')
        compute.run(service)
      # Delete the service now, so that the temp directory is cleaned up, so
      # the warning is captured now, in the context
      del service

  def test_run_simple(self):
    compute = virtualenv.Compute()
    service = MockVirtualEnvService()

    self.return_value = 0
    compute.run(service)

    self.assertEqual(self.popen_args, (['ls'],))
    # Only kwarg is env
    self.assertEqual(set(self.popen_kwargs.keys()), {'env', 'executable'})
    self.assertEqual(self.popen_kwargs['env']['BAR'], 'FOO')

  def test_run_virtualenv(self):
    compute = virtualenv.Compute()
    service = MockVirtualEnvService()

    with settings:
      settings.compute.virtualenv_dir = "/bar/foo"

      self.return_value = 0
      with self.assertLogs(virtualenv.__name__, level="WARNING") as cm:
        compute.run(service)
      self.assertTrue(any("Couldn't find command ls in virtualenv_dir" in x
                          for x in cm.output))

    self.assertEqual(self.popen_args, (['ls'],))
    self.assertEqual(set(self.popen_kwargs.keys()), {'env', 'executable'})
    self.assertEqual(self.popen_kwargs['env']['BAR'], 'FOO')
    self.assertTrue(self.popen_kwargs['env']['PATH'].startswith('/bar/foo'))

  def test_logging_code(self):
    compute = virtualenv.Compute()
    service = MockVirtualEnvService()

    # Test logging code
    with self.assertLogs(virtualenv.__name__, level="DEBUG4") as cm:
      os.environ['BAR'] = 'FOO'
      env = os.environ.copy()
      env.pop('BAR')
      env['FOO'] = 'BAR'
      service.env = env

      self.return_value = 0
      compute.run(service)

    env_lines = [x for x in cm.output if "Environment Modification:" in x][0]
    env_lines = env_lines.split('\n')
    self.assertEqual(len(env_lines), 5)

    self.assertTrue(any(o.startswith('- BAR:') for o in env_lines))
    self.assertTrue(any(o.startswith('+ FOO:') for o in env_lines))
    # Added by Terra
    self.assertTrue(any(o.startswith('+ TERRA_SETTINGS_FILE:')
                        for o in env_lines))
    # Added by TestSettingsConfigureCase
    self.assertTrue(any(o.startswith('- TERRA_SETTINGS_FILE:')
                        for o in env_lines))
