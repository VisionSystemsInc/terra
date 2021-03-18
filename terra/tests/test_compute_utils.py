import ntpath
import pathlib
import posixpath
import os
from unittest import mock
import warnings

from terra import settings
from .utils import TestSettingsConfigureCase
import terra.compute.utils as utils
import terra.compute.dummy
import terra.compute.docker
import terra.compute.base


# A test compute based off of dummy, but not dummy. These two classes turn this
# test into an official terra compute definition
class Compute(terra.compute.dummy.Compute):
  pass


class Service:
  pass


class Service_test:
  pass


class Service2:
  pass


class Service2_test:
  pass


# I am purposefully showing multiple ways to mock _wrapped for demonstration
# purposes
class TestComputeUtilsCase(TestSettingsConfigureCase):
  def setUp(self):
    # Use setting
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    # For registering a service
    self.patches.append(mock.patch.dict(terra.compute.base.services,
                                        clear=True))
    self.config.compute = {'arch': Compute.__module__}

    super().setUp()

    # Manually register this Compute without using decorator
    Compute.register(Service)(Service_test)
    # Manually register against base compute. Normally this is never done, but
    # done for some core case tests below
    terra.compute.base.BaseCompute.register(Service2)(Service2_test)


class TestUtils(TestComputeUtilsCase):
  def test_compute_handler_from_settings(self):
    # Test handler working
    self.assertIsInstance(utils.ComputeHandler()._connection, Compute)

  # I don't want setUp's configure for this test
  @mock.patch.object(settings, '_wrapped', None)
  def test_compute_handler_from_override(self):
    settings.configure({})
    self.assertIsInstance(utils.ComputeHandler()._connection,
                          terra.compute.dummy.Compute)
    self.assertIsInstance(
        utils.ComputeHandler(Compute.__module__)._connection, Compute)

  # I don't want setUp's configure for this test
  @mock.patch.object(settings, '_wrapped', None)
  def test_compute_handler_short_name(self):
    # Since the "docker" library is installed, this test actually imports
    # docker before importing the real docker Compute, hence the warning.
    settings.configure({'compute': {'arch': 'docker'}})
    # Suppress imp warnings caused by docker
    with warnings.catch_warnings():
      warnings.simplefilter('ignore')
      # Make sure it worked
      self.assertIsInstance(utils.ComputeHandler()._connection,
                            terra.compute.docker.Compute)

  def test_get_default_service(self):
    # Make sure service definition works too
    self.assertIs(utils.get_default_service_class(Compute), Service)

  def test_load_service_by_instance(self):
    service = Service()
    self.assertIs(utils.load_service(service), service)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_by_class(self):
    self.assertIsInstance(utils.load_service(Service), Service_test)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_by_str(self):
    self.assertIsInstance(utils.load_service(Service.__module__ + '.Service'),
                          Service_test)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_by_str_using_default_implementation(self):
    self.assertIsInstance(utils.load_service(Service.__module__ + '.Service2'),
                          Service)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_unregistered(self):
    with self.assertRaises(KeyError), self.assertLogs(utils.__name__) as log:
      utils.load_service(__name__)

    self.assertIn(f'{__name__} is not registered', str(log.output))


class TestComputeHandler(TestComputeUtilsCase):
  @mock.patch.object(settings, '_wrapped', None)
  def test_compute_handler(self):
    settings.configure({'compute': {'arch': 'terra.compute.dummy'}})
    test_compute = utils.ComputeHandler()
    self.assertIsInstance(test_compute._connection,
                          terra.compute.dummy.Compute)

  # Make sure this can be run twice
  test_compute_handler2 = test_compute_handler


# Dummy mock to double check args
def mock_popen(*args, **kwargs):
  return (args, kwargs)


class TestBaseJust(TestComputeUtilsCase):
  def setUp(self):
    # Make a copy
    self.original_env = os.environ.copy()

    self.patches.append(mock.patch.object(utils, 'Popen', mock_popen))
    super().setUp()

  def tearDown(self):
    super().tearDown()
    # Make sure nothing inadvertently changed environ
    self.assertEqual(self.original_env, os.environ)

  def test_just_simple(self):
    default_justfile = os.path.join(os.environ['TERRA_TERRA_DIR'], 'Justfile')
    # Call just, and get the args calculated, retrieved via mock
    args, kwargs = utils.just("foo  bar")
    self.assertEqual(args, (('bash', 'just', 'foo  bar'),))
    self.assertEqual(set(kwargs.keys()), {'executable', 'env'})
    self.assertEqual(kwargs['env']['JUSTFILE'], default_justfile)

  def test_just_custom_env(self):
    default_justfile = os.path.join(os.environ['TERRA_TERRA_DIR'], 'Justfile')
    # Use the env kwarg
    args, kwargs = utils.just("foo", "bar", env={"FOO": "BAR"})
    self.assertEqual(args, (('bash', 'just', 'foo', 'bar'),))
    self.assertEqual(set(kwargs.keys()), {'executable', 'env'})
    self.assertTrue(kwargs.pop('executable').endswith('bash'))
    self.assertEqual(kwargs, {'env': {'FOO': 'BAR',
                                      'JUSTFILE': default_justfile}})

  def test_just_custom_justfile(self):
    # Use the justfile kwarg
    args, kwargs = utils.just("foobar", justfile="/foo/bar")
    self.assertEqual(args, (('bash', 'just', 'foobar'),))
    self.assertEqual(set(kwargs.keys()), {'executable', 'env'})
    self.assertEqual(kwargs['env']['JUSTFILE'], "/foo/bar")

  def test_just_kwargs(self):
    default_justfile = os.path.join(os.environ['TERRA_TERRA_DIR'], 'Justfile')
    # Use the shell kwarg for Popen
    args, kwargs = utils.just("foobar", shell=False)
    self.assertEqual(args, (('bash', 'just', 'foobar'),))
    self.assertEqual(set(kwargs.keys()), {'executable', 'env', 'shell'})
    self.assertEqual(kwargs['shell'], False)
    self.assertEqual(kwargs['env']['JUSTFILE'], default_justfile)

  def test_logging_code(self):
    # Test the debug1 diffdict log output
    with self.assertLogs(utils.__name__, level="DEBUG4") as cm:
      env = os.environ.copy()
      env.pop('PATH')
      env['FOO'] = 'BAR'
      # Sometimes JUSTFILE is set, so make this part of the test!
      with mock.patch.dict(os.environ, JUSTFILE='/foo/bar'):
        utils.just("foo", "bar", env=env)

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


class TestTranslateUtils(TestComputeUtilsCase):

  def _nt_or_posix(self, nt_obj, posix_obj, platform):
    return nt_obj if platform in ('windows', 'nt') else posix_obj

  def _drive(self, host_platform, container_platform):
    return (self._nt_or_posix('H:\\', '/', host_platform),
            self._nt_or_posix('C:\\', '/', container_platform))

  def _os(self, host_platform, container_platform):
    return (self._nt_or_posix(ntpath, posixpath, host_platform),
            self._nt_or_posix(ntpath, posixpath, container_platform))

  def _create_volume_map(self, host_platform, container_platform):

    # test data
    test_data = [
        (('src', 'abc'), ('dst', 'ABC')),
        (('src', 'abc_output'), ('dst', 'OUTPUT')),
        (('src', 'def'), ('dst', 'DEF')),
        (('src', 'abc.json'), ('dst', 'ABC.json')),
    ]

    # append "drive" to test data
    host_drv, container_drv = self._drive(host_platform, container_platform)
    test_data = [((host_drv, *src), (container_drv, *dst))
                 for src, dst in test_data]

    # volume map
    host_os, container_os = self._os(host_platform, container_platform)
    volume_map = [(host_os.join(*src), container_os.join(*dst))
                  for src, dst in test_data]
    return volume_map

  def _test_pathlib_map(self, container_platform):
    host_obj_type = type(pathlib.Path())
    container_obj_type = self._nt_or_posix(pathlib.PureWindowsPath,
                                           pathlib.PurePosixPath,
                                           container_platform)

    volume_map = self._create_volume_map(os.name, container_platform)
    pathlib_map = utils.pathlib_map(volume_map, container_platform)

    for host_obj, container_obj in pathlib_map:
      self.assertIsInstance(host_obj, host_obj_type)
      self.assertIsInstance(container_obj, container_obj_type)

  def test_pathlib_map_linux(self):
    self._test_pathlib_map('linux')

  def test_pathlib_map_windows(self):
    self._test_pathlib_map('windows')

  def _test_patch_volume(self, container_platform):
    volume_map = self._create_volume_map(os.name, container_platform)
    host_os, container_os = self._os(os.name, container_platform)

    for host_vol, container_vol in volume_map:
      is_file = '.' in pathlib.Path(host_vol).parts[-1]
      if is_file:
        # direct file mapping only
        test_items = [[]]
      else:
        # this directory, subdirectory, and file mappings
        test_items = [[], ['xyz'], ['xyz', 'xyz']]
        test_items += [[*ti, 'file.json'] for ti in test_items]

      for item in test_items:
        host_item = host_os.join(host_vol, *item)
        container_item = container_os.join(container_vol, *item)
        result = utils.patch_volume(host_item, volume_map, container_platform)
        self.assertEqual(result, container_item)

  def test_patch_volume_linux(self):
    self._test_patch_volume('linux')

  def test_patch_volume_windows(self):
    self._test_patch_volume('windows')

  @mock.patch.dict(os.environ, FOO='/foo/bar', BAR='bar')
  def test_patch_volume_expand(self):
    # Test variable expansion and user home dir expansion
    volume_map = [('/foo/bar', '/dst')]
    self.assertEqual(utils.patch_volume('${FOO}/baz', volume_map, 'linux'),
                     '/dst/baz')
    self.assertEqual(utils.patch_volume('/foo/${BAR}/car',
                                        volume_map,
                                        'linux'),
                     '/dst/car')
    volume_map = [(os.path.expanduser('~'), '/myhome')]
    self.assertEqual(utils.patch_volume('~/${BAR}/car', volume_map, 'linux'),
                     '/myhome/bar/car')
