import os
from unittest import mock
import tempfile

from terra import settings
from terra.compute import base
from terra.compute import virtualenv
import terra.compute.utils

from .utils import TestCase


class MockVirtalEnvService(virtualenv.Service):
  def __init__(self):
    super().__init__()
    self.command = ["ls"]
    self.env["BAR"] = "FOO"


class TestVirtualEnv(TestCase):
  def setUp(self):
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    # This will resets the _connection to an uninitialized state
    self.patches.append(
        mock.patch.object(
            terra.compute.utils.ComputeHandler,
            '_connection',
            mock.PropertyMock(return_value=virtualenv.Compute())))

    self.patches.append(mock.patch.object(virtualenv,
                                          'Popen', self.mock_popen))

    # patches.append(mock.patch.dict(base.services, clear=True))
    super().setUp()
    settings.configure({
        'compute': {'arch': 'virtualenv'},
        'processing_dir': self.temp_dir.name,
        'test_dir': '/opt/projects/terra/terra_dsm/external/terra/foo'})

  def mock_popen(_self, *args, **kwargs):
    _self.popen_args = args
    _self.popen_kwargs = kwargs
    return type('blah', (object,), {'wait': lambda self: _self.return_value})()

  def test_run(self):
    compute = virtualenv.Compute()
    service = MockVirtalEnvService()

    self.return_value = 1
    with self.assertRaises(base.ServiceRunFailed):
      compute.run(service)

    self.return_value = 0
    compute.run(service)
    self.assertEqual(self.popen_args, (['ls'],))
    self.assertEqual(set(self.popen_kwargs.keys()), {'env'})
    self.assertEqual(self.popen_kwargs['env']['BAR'], 'FOO')

    with settings:
      settings.compute.virtualenv_dir = "/bar/foo"
      compute.run(service)
      self.assertEqual(self.popen_args, (['ls'],))
      self.assertEqual(set(self.popen_kwargs.keys()), {'env'})
      self.assertEqual(self.popen_kwargs['env']['BAR'], 'FOO')
      self.assertTrue(self.popen_kwargs['env']['PATH'].startswith('/bar/foo'))

    # Test logging code
    with self.assertLogs(virtualenv.__name__, level="DEBUG1") as cm:
      env = os.environ.copy()
      env.pop('PATH')
      env['FOO'] = 'BAR'
      service.env = env
      compute.run(service)

    env_lines = [x for x in cm.output if "Environment Modification:" in x][0]
    env_lines = env_lines.split('\n')
    self.assertEqual(len(env_lines), 3)

    self.assertTrue(any(o.startswith('- PATH:') for o in env_lines))
    self.assertTrue(any(o.startswith('+ FOO:') for o in env_lines))
