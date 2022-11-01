import os
from unittest import mock

from terra.compute import base
from terra.compute import singularity
import terra.compute.utils

from .utils import TestSettingsConfigureCase


class TestComputeSingularityCase(TestSettingsConfigureCase):
  def setUp(self):
    # This will reset the _connection to an uninitialized state
    self.patches.append(
        mock.patch.object(terra.compute.utils.ComputeHandler,
                          '_connection',
                          mock.PropertyMock(
                              return_value=singularity.Compute())))
    # Configure for singularity
    self.config.compute = {'arch': 'singularity'}
    super().setUp()


class MockJustService:
  def __init__(self):
    self.compose_files = ["file1"]
    self.compose_service_name = "launch"
    self.command = ["ls"]
    self.env = {"BAR": "FOO", 'TERRA_SETTINGS_FILE': '/foo/bar'}


class TestSingular(TestComputeSingularityCase):
  def mock_just(_self, *args, **kwargs):
    _self.just_args = args
    _self.just_kwargs = kwargs
    return type('blah', (object,), {'wait': lambda self: _self.return_value})()

  def setUp(self):
    # Mock the just call for recording
    self.patches.append(mock.patch.object(singularity, 'just',
                                          self.mock_just))
    super().setUp()

  def test_run(self):
    compute = singularity.Compute()

    self.return_value = 0
    # This part of the test looks fragile
    compute.run(MockJustService())
    # Run a singularity service
    self.assertEqual(('singular-compose', '--file', 'file1', 'run',
                      'launch', 'ls'),
                     self.just_args)
    self.assertEqual({'env': {'BAR': 'FOO',
                              'SINGULARITYENV_TERRA_SETTINGS_FILE': '/foo/bar',
                              'TERRA_SETTINGS_FILE': '/foo/bar'}},
                     self.just_kwargs)

    # Test a non-zero return value
    self.return_value = 1
    with self.assertRaises(base.ServiceRunFailed):
      compute.run(MockJustService())

  def test_run_multiple_compose_files(self):
    compute = singularity.Compute()

    self.return_value = 0
    # This part of the test looks fragile
    service = MockJustService()
    service.compose_files = service.compose_files + ['file_too', 'fileThree']
    compute.run(service)
    # Run a singularity service
    self.assertEqual(('singular-compose', '--file', 'file1', '--file',
                      'file_too', '--file', 'fileThree', 'run', 'launch', 'ls'),
                     self.just_args)
    self.assertEqual({'env': {'BAR': 'FOO',
                              'SINGULARITYENV_TERRA_SETTINGS_FILE': '/foo/bar',
                              'TERRA_SETTINGS_FILE': '/foo/bar'}},
                     self.just_kwargs)

    # Test a non-zero return value
    self.return_value = 1
    with self.assertRaises(base.ServiceRunFailed):
      compute.run(MockJustService())


class TestSingularityConfig(TestComputeSingularityCase):
  def setUp(self):
    # Mock the just call for recording
    self.patches.append(mock.patch.object(singularity, 'just',
                                          self.mock_just_config))
    super().setUp()

  # Create a special mock functions that takes the Tests self as _self, and the
  # rest of the args as args/kwargs. This lets me do testing inside the mocked
  # function.
  def mock_just_config(_self, *args, **kwargs):
    _self.just_args = args
    _self.just_kwargs = kwargs
    return type('blah', (object,),
                {'communicate':
                 lambda self: (b'environment\0^foo\0.bar\0^stuff\0^boo\0.far',
                               None)})()

  def test_config(self):
    compute = singularity.Compute()

    self.assertEqual(compute.config(MockJustService()),
                     {'environment': {'foo': 'bar'}, 'stuff': ['boo', 'far']})
    self.assertEqual(('singular-compose', '--file', 'file1',
                      'config-null', 'launch'), self.just_args)

    self.assertEqual({'stdout': singularity.PIPE,
                      'env': {'BAR': 'FOO', 'TERRA_SETTINGS_FILE': '/foo/bar'},
                      'justfile': None},
                     self.just_kwargs)

  def test_config_with_multiple_compose_files(self):
    compute = singularity.Compute()
    service = MockJustService()
    service.compose_files = service.compose_files + ['file15.env', 'file2.env']
    self.assertEqual(compute.config_service(service),
                     {'environment': {'foo': 'bar'}, 'stuff': ['boo', 'far']})
    self.assertEqual(('singular-compose', '--file', 'file1',
                      '--file', 'file15.env', '--file', 'file2.env',
                      'config-null', 'launch'),
                     self.just_args)
    self.assertEqual({'stdout': singularity.PIPE,
                      'env': {'BAR': 'FOO', 'TERRA_SETTINGS_FILE': '/foo/bar'},
                      'justfile': None},
                     self.just_kwargs)


def mock_config(self, service_info, *args, **kwargs):
  if service_info.compose_service_name == "foo":
    return {'volumes': []}
  elif service_info.compose_service_name == "bar":
    return {'volumes': [
        '/tmp:/bar',
        '/opt/projects/terra/terra_dsm/external/terra:/src',
        '/opt/projects/terra/terra_dsm/external/terra:/terra',
        '/tmp/.X11-unix:/tmp/.X11-unix',
        '/opt/projects/terra/terra_dsm/external/terra/external/vsi_common:'
        '/vsi']}
  elif service_info.compose_service_name == "test":
    return {'volumes': ['/tmp\\:/bar',
                        '/tmp/.X11-unix/:/tmp/.X11-unix']}


class TestSingularityMap(TestComputeSingularityCase):
  class Service:
    compose_service_name = "foo"
    volumes = []

  @mock.patch.object(singularity.Compute, 'config_service', mock_config)
  def test_config_non_existing_service(self):
    compute = singularity.Compute()
    service = TestSingularityMap.Service()

    volume_map = compute.configuration_map(service)
    # Should be empty
    self.assertEqual(volume_map, [])

  @mock.patch.object(singularity.Compute, 'config_service', mock_config)
  def test_config_terra_service(self):
    compute = singularity.Compute()
    service = TestSingularityMap.Service()

    service.compose_service_name = "bar"
    volume_map = compute.configuration_map(service)
    ans = [('/tmp', '/bar'),
           ('/opt/projects/terra/terra_dsm/external/terra', '/src'),
           ('/opt/projects/terra/terra_dsm/external/terra', '/terra'),
           ('/tmp/.X11-unix', '/tmp/.X11-unix'),
           ('/opt/projects/terra/terra_dsm/external/terra/external/vsi_common',
            '/vsi')]
    self.assertEqual(volume_map, ans)

  @mock.patch.object(singularity.Compute, 'config_service', mock_config)
  @mock.patch.object(os, 'name', 'posix')
  def test_config_test_service(self):
    compute = singularity.Compute()
    service = TestSingularityMap.Service()

    service.compose_service_name = "test"
    volume_map = compute.configuration_map(service)
    ans = [('/tmp\\', '/bar'),
           ('/tmp/.X11-unix', '/tmp/.X11-unix')]
    self.assertEqual(volume_map, ans)

  @mock.patch.object(singularity.Compute, 'config_service', mock_config)
  @mock.patch.object(os, 'name', 'nt')
  def test_config_test_service_nt(self):
    compute = singularity.Compute()
    service = TestSingularityMap.Service()

    service.compose_service_name = "test"
    volume_map = compute.configuration_map(service)
    ans = [('/tmp', '/bar'),
           ('/tmp/.X11-unix', '/tmp/.X11-unix')]
    self.assertEqual(volume_map, ans)
