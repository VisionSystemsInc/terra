import os
from unittest import mock

from terra import settings
# from terra.compute import base
from terra.compute import just
from terra.compute import compute
import terra.compute.utils
from .utils import TestCase

class TestComputeJustCase(TestCase):
  def setUp(self):
    # Use settings
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    # This will resets the _connection to an uninitialized state
    self.patches.append(
        mock.patch.object(terra.compute.utils.ComputeHandler,
                          '_connection',
                          mock.PropertyMock(return_value=just.JustCompute())))

    # patches.append(mock.patch.dict(base.services, clear=True))
    super().setUp()

    # Configure for base
    settings.configure({
        'compute': {'arch': 'mocked_out'},
        'processing_dir': self.temp_dir.name,
        'test_dir': '/opt/projects/terra/terra_dsm/external/terra/foo'})


# Dummy mock to double check args
def mock_popen(*args, **kwargs):
  return (args, kwargs)


class TestBaseJust(TestComputeJustCase):
  def setUp(self):
    self.patches.append(mock.patch.object(just, 'Popen', mock_popen))
    super().setUp()
    # Make a copy
    self.original_env = os.environ.copy()

  def tearDown(self):
    super().tearDown()
    # Make sure nothing inadvertently changed environ
    self.assertEqual(self.original_env, os.environ)

  def test_just_simple(self):
    default_justfile = os.path.join(os.environ['TERRA_TERRA_DIR'], 'Justfile')
    # Create a compute
    compute = just.JustCompute()
    # Call just, and get the args calculated, retrieved via mock
    args, kwargs = compute.just("foo  bar")
    self.assertEqual(args, (('bash', 'just', 'foo  bar'),))
    self.assertEqual(set(kwargs.keys()), {'executable', 'env'})
    self.assertEqual(kwargs['env']['JUSTFILE'], default_justfile)

  def test_just_custom_env(self):
    default_justfile = os.path.join(os.environ['TERRA_TERRA_DIR'], 'Justfile')
    # Use the env kwarg
    args, kwargs = compute.just("foo", "bar", env={"FOO": "BAR"})
    self.assertEqual(args, (('bash', 'just', 'foo', 'bar'),))
    self.assertEqual(set(kwargs.keys()), {'executable', 'env'})
    self.assertTrue(kwargs.pop('executable').endswith('bash'))
    self.assertEqual(kwargs, {'env': {'FOO': 'BAR',
                                      'JUSTFILE': default_justfile}})

  def test_just_custom_justfile(self):
    # Use the justfile kwarg
    args, kwargs = compute.just("foobar", justfile="/foo/bar")
    self.assertEqual(args, (('bash', 'just', 'foobar'),))
    self.assertEqual(set(kwargs.keys()), {'executable', 'env'})
    self.assertEqual(kwargs['env']['JUSTFILE'], "/foo/bar")

  def test_just_kwargs(self):
    default_justfile = os.path.join(os.environ['TERRA_TERRA_DIR'], 'Justfile')
    # Use the shell kwarg for Popen
    args, kwargs = compute.just("foobar", shell=False)
    self.assertEqual(args, (('bash', 'just', 'foobar'),))
    self.assertEqual(set(kwargs.keys()), {'executable', 'env', 'shell'})
    self.assertEqual(kwargs['shell'], False)
    self.assertEqual(kwargs['env']['JUSTFILE'], default_justfile)

  def test_logging_code(self):
    # Test the debug1 diffdict log output
    with self.assertLogs(just.__name__, level="DEBUG1") as cm:
      env = os.environ.copy()
      env.pop('PATH')
      env['FOO'] = 'BAR'
        # Sometimes JUSTFILE is set, so make this part of the test!
      with mock.patch.dict(os.environ, JUSTFILE='/foo/bar'):
        compute.just("foo", "bar", env=env)

    env_lines = [x for x in cm.output if "Environment Modification:" in x][0]
    env_lines = env_lines.split('\n')
    self.assertEqual(len(env_lines), 5, env_lines)

    # Verify logs say PATH was removed
    self.assertTrue(any(o.startswith('- PATH:') for o in env_lines))
    # FOO was added
    self.assertTrue(any(o.startswith('+ FOO:') for o in env_lines))
    # JUSTFILE was changed
    self.assertTrue(any(o.startswith('+ JUSTFILE:') for o in env_lines))
    self.assertTrue(any(o.startswith('- JUSTFILE:') for o in env_lines))
