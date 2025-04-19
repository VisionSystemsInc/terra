import os
import ntpath
import json
from unittest import mock, skipIf

from terra import settings
from terra.executor.utils import Executor
from terra.compute import base
import terra.compute.container
from .utils import TestNamedTemporaryFileCase, TestSettingsConfigureCase


class SomeService(terra.compute.container.ContainerService):
  def __init__(self, compose_service_name="launch", compose_file="file1",
               command=["ls"], env={"BAR": "FOO"}):
    self.compose_service_name = compose_service_name
    self.compose_files = [compose_file]
    self.command = command
    self.env = env
    super().__init__()


def mock_map(self, *args, **kwargs):
  return [('/foo', '/bar'),
          ('/tmp/.X11-unix', '/tmp/.X11-unix')]


def mock_map_lcow(self, *args, **kwargs):
  return [('/c/foo', '/bar')]


class TestComputeContainerCase(TestSettingsConfigureCase):
  def setUp(self):
    self.temp_dir
    # This will resets the _connection to an uninitialized state
    self.patches.append(
        mock.patch.object(terra.compute.utils.ComputeHandler,
                          '_connection',
                          mock.PropertyMock(return_value=base.BaseCompute())))

    # Configure for base
    self.config.compute = {'arch': 'terra.compute.base.BaseCompute'}

    # patches.append(mock.patch.dict(base.services, clear=True))
    super().setUp()


class TestContainerService(TestComputeContainerCase,
                           TestNamedTemporaryFileCase):
  # Test the flushing configuration to json for a container mechanism

  def setUp(self):
    self.patches.append(mock.patch.object(json, 'dump', self.json_dump))
    # self.common calls service.pre_run which trigger Executor
    self.patches.append(mock.patch.dict(Executor.__dict__))
    super().setUp()

  def json_dump(self, config, fid):
    self.config = config

  def common(self, compute, service):
    with open(settings.logging.server.listen_address, 'w'):
      pass

    service.pre_run()
    setup_dir = service.temp_dir.name
    config = self.config

    # Test that foo_dir has been translated
    self.assertEqual(config['foo_dir'], '/bar',
                     'Path translation test failed')
    # Test that bar_dir has not changed
    self.assertEqual(config['bar_dir'], '/not_foo',
                     'Nontranslated directory failure')
    # Verify the setting files is pointed to correctly
    self.assertEqual(service.env['TERRA_SETTINGS_FILE'],
                     "/tmp_settings/config.json",
                     'Failure to set TERRA_SETTINGS_FILE')
    # Clean up temp file
    service.post_run()

    # Test that the config dir was set to be mounted
    self.assertIn(f'{setup_dir}:/tmp_settings',
                  (v for k, v in service.env.items()
                   if k.startswith('TERRA_VOLUME_')),
                  'Configuration failed to injected into container')

  @skipIf(os.name != "posix", 'Requires Linux')
  @mock.patch.object(base.BaseCompute, 'configuration_map_service', mock_map)
  def test_service_simple(self):
    with mock.patch.dict(settings._wrapped, {}):
      compute = base.BaseCompute()
      compute.configuration_map(SomeService())

      # Test setting for translation
      settings.foo_dir = "/foo"  # From mock_map
      settings.bar_dir = "/not_foo"

      service = SomeService()
      # Simple case
      self.common(compute, service)

  @skipIf(os.name != "nt", "Requires Windows")
  @mock.patch.object(base.BaseCompute, 'configuration_map_service', mock_map)
  def test_service_simple_nt(self):
    # Test and code not fully written yet?
    with mock.patch.dict(settings._wrapped, {}):
      compute = base.BaseCompute()
      compute.configuration_map(SomeService())

      # Test setting for translation
      settings.foo_dir = "/C/FoO"  # From mock_map
      settings.bar_dir = "/not_foo"

      service = SomeService()
      # Simple case
      self.common(compute, service)

  @skipIf(os.name != "posix", "Required Linux")
  @mock.patch.object(base.BaseCompute, 'configuration_map_service', mock_map)
  def test_service_other_dir_methods(self):
    compute = base.BaseCompute()
    compute.configuration_map(SomeService())

    # Test setting for translation
    settings.foo_dir = "/foo"
    settings.bar_dir = "/not_foo"

    # Run same tests with a TERRA_VOLUME externally set
    service = SomeService()
    service.add_volume('/test1', '/test2', 'z')
    service.env['TERRA_VOLUME_1'] = "/Foo:/Bar"
    self.common(compute, service)
    # Make sure this is still set correctly
    self.assertEqual(service.env['TERRA_VOLUME_1'], "/Foo:/Bar")
    self.assertIn('/test1:/test2:z',
                  (v for k, v in service.env.items()
                   if k.startswith('TERRA_VOLUME_')),
                  'Added volume failed to be bound')


class TestContainerService2(TestComputeContainerCase):
  def test_add_volume(self):
    service = SomeService()
    self.assertEqual(service.volumes, [])

    service.add_volume('/foo', '/bar')
    self.assertEqual(service.volumes, [('/foo', '/bar')])
    self.assertEqual(service.volumes_flags, [None])

    service.add_volume('/data', '/testData', 'ro')
    self.assertEqual(service.volumes, [('/foo', '/bar'),
                                       ('/data', '/testData')])
    self.assertEqual(service.volumes_flags, [None, 'ro'])

    service.add_volume('/boo', '/far', prefix="/car")
    self.assertEqual(service.volumes, [('/foo', '/bar'),
                                       ('/data', '/testData'),
                                       ('/boo', '/car/far')])
    self.assertEqual(service.volumes_flags, [None, 'ro', None])

  @mock.patch.object(os, 'name', 'nt')
  @mock.patch.object(os, 'path', ntpath)
  def test_add_volume_nt_wcow(self):
    service = SomeService()
    self.assertEqual(service.volumes, [])

    service.container_platform = 'windows'

    service.add_volume(r'c:\foo', r'd:\bar', prefix='/car')
    self.assertEqual(service.volumes, [(r'c:\foo', r'd:\car\bar')])

  @mock.patch.object(os, 'name', 'nt')
  @mock.patch.object(os, 'path', ntpath)
  def test_add_volume_nt_lcow(self):
    service = SomeService()
    self.assertEqual(service.volumes, [])

    service.container_platform = 'linux'

    service.add_volume(r'c:\foo', r'd:\bar', prefix='/car')
    self.assertEqual(service.volumes, [(r'c:\foo', '/car/d/bar')])
