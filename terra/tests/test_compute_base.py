import os
import tempfile
from unittest import mock

from terra import settings
import terra.compute.base
from .utils import (
  TestCase, TestSettingsConfigureCase, TestSettingsUnconfiguredCase
)


class TestServiceBase(TestSettingsConfigureCase):
  # Simulate external env var
  @mock.patch.dict(os.environ, {'FOO': "BAR"})
  def test_env(self):
    # Test that a service inherits the environment correctly
    service = terra.compute.base.BaseService()
    # App specific env var
    service.env['BAR'] = 'foo'
    # Make sure both show up
    self.assertEqual(service.env['FOO'], 'BAR')
    self.assertEqual(service.env['BAR'], 'foo')
    # Make sure BAR is isolated from process env
    self.assertNotIn("BAR", os.environ)

  def test_add_volumes(self):
    service = terra.compute.base.BaseService()
    # Add a volumes
    service.add_volume("/local", "/remote")
    # Make sure it's in the list
    self.assertIn(("/local", "/remote"), service.volumes)

  def test_create_service_dir(self):
    # first create a temp dir
    with tempfile.TemporaryDirectory() as foo_dir:

      service = terra.compute.base.BaseService()
      overwrite = False
      # a Runtime error should occur because the directory exists and overwrite is false
      with self.assertRaises(RuntimeError):
        service.create_service_dir(foo_dir, overwrite)

      # set overwrite to true
      overwrite = True
      # create a subdir to test overwriting the directory
      # only the contents of the service dir are overwritten
      foo_sub_dir = os.path.join(foo_dir, 'service_dir')
      os.makedirs(foo_sub_dir, exist_ok=True)
      service.create_service_dir(foo_dir, overwrite)
      # foo dir should now be empty
      dirs = os.listdir(foo_dir)
      self.assertEqual(len(dirs), 0)

      # since the sub service dir was removed, test creating it wit create_service_dir
      service.create_service_dir(foo_sub_dir, overwrite)
      # foo dir should now have a sub directory
      dirs = os.listdir(foo_dir)
      self.assertEqual(len(dirs), 1)

  def test_registry(self):
    with mock.patch.dict(terra.compute.base.services, clear=True):
      # Registration test
      class Foo:
        class TestService(terra.compute.base.BaseService):
          pass

      class TestService_base(Foo.TestService, terra.compute.base.BaseService):
        pass

      # Register a class class, just for fun
      terra.compute.base.BaseCompute.register(Foo.TestService)(
          TestService_base)

      self.assertIn(Foo.TestService.__module__ + '.'
                    + Foo.TestService.__qualname__,
                    terra.compute.base.services)

      with self.assertRaises(terra.compute.base.AlreadyRegisteredException,
                             msg='Compute command "car" does not have a '
                                 'service implementation "car_service"'):
        terra.compute.base.BaseCompute.register(Foo.TestService)(lambda x: 1)

  def test_getattr(self):
    class Foo(terra.compute.base.BaseCompute):
      def bar_service(self):
        pass

    foo = Foo()
    foo.bar
    with self.assertRaises(AttributeError):
      foo.car


class TestServiceBaseUnconfigured(TestSettingsUnconfiguredCase):
  def test_volumes_and_configuration_map(self):
    # Add a volumes
    service = terra.compute.base.BaseService()
    service.add_volume("/local", "/remote")

    # Test configuration_map
    settings.configure({})
    # Make sure the volume is in the map
    self.assertEqual(
        [("/local", "/remote")],
        terra.compute.base.BaseCompute().configuration_map(service))


class TestUnitTests(TestCase):
  def last_test_registered_services(self):
    self.assertFalse(
      terra.compute.base.services,
      msg="If you are seeing this, one of the other unit tests has "
      "registered a terra service. This side effect should be "
      "prevented by mocking out the terra.compute.base.services dict. "
      "Otherwise unit tests can interfere with each other.")
