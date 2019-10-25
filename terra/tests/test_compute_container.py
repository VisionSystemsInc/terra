import os
import json
from unittest import mock

from terra import settings
from terra.compute import docker

from .test_compute_docker import TestComputeDockerCase


class SomeService(docker.Service):
  def __init__(self, compose_service_name="launch", compose_file="file1",
               command=["ls"], env={"BAR": "FOO"}):
    self.compose_service_name = compose_service_name
    self.compose_file = compose_file
    self.command = command
    self.env = env
    super().__init__()


def mock_map(self, *args, **kwargs):
  return [('/foo', '/bar'),
          ('/tmp/.X11-unix', '/tmp/.X11-unix')]


class TestDockerService(TestComputeDockerCase):
  # Test the flushing configuration to json for a container mechanism

  def common(self, compute, service):
    service.pre_run()
    setup_dir = service.temp_dir.name
    with open(os.path.join(setup_dir, 'config.json'), 'r') as fid:
      config = json.load(fid)

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
    self.assertIn(f'{setup_dir}:/tmp_settings:rw',
                  (v for k, v in service.env.items()
                   if k.startswith('TERRA_VOLUME_')),
                  'Configuration failed to injected into docker')

  @mock.patch.object(docker.Compute, 'configuration_map_service', mock_map)
  def test_service_simple(self):
    # Must not be a decorator, because at decorator time (before setUp is run),
    # settings._wrapped is still None. Mock the version from setUpModule so I
    # change the values without affecting any other test
    with mock.patch.dict(settings._wrapped, {}):
      compute = docker.Compute()
      compute.configuration_map(SomeService())

      # Test setting for translation
      settings.foo_dir = "/foo"
      settings.bar_dir = "/not_foo"

      service = SomeService()
      # Simple case
      self.common(compute, service)

  @mock.patch.object(docker.Compute, 'configuration_map_service', mock_map)
  def test_service_other_dir_methods(self):
    compute = docker.Compute()
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
