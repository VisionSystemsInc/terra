import os
from unittest import mock

from terra import settings
from .utils import TestCase, TestSettingsConfiguredCase


class TestServiceBase(TestSettingsConfiguredCase):
  def setUp(self):
    from terra.compute import base
    self.base = base
    super().setUp()

  # Simulate external env var
  @mock.patch.dict(os.environ, {'FOO': "BAR"})
  def test_env(self):
    # Test that a service inherits the environment correctly
    service = self.base.BaseService()
    # App specific env var
    service.env['BAR'] = 'foo'
    # Make sure both show up
    self.assertEqual(service.env['FOO'], 'BAR')
    self.assertEqual(service.env['BAR'], 'foo')
    # Make sure BAR is isolated from process env
    self.assertNotIn("BAR", os.environ)

  def test_add_volumes(self):
    service = self.base.BaseService()
    # Add a volumes
    service.add_volume("/local", "/remote")
    # Make sure it's in the list
    self.assertIn(("/local", "/remote"), service.volumes)

  # Unconfigure settings
  @mock.patch.object(settings, '_wrapped', None)
  def test_volumes_and_configuration_map(self):
    # Add a volumes
    service = self.base.BaseService()
    service.add_volume("/local", "/remote")

    # Test configuration_map
    settings.configure({})
    # Make sure the volume is in the map
    self.assertEqual([("/local", "/remote")],
                     self.base.BaseCompute().configuration_map(service))

  def test_registry(self):
    with mock.patch.dict(self.base.services, clear=True):
      # Registration test
      class Foo:
        class TestService(self.base.BaseService):
          pass


      class TestService_base(Foo.TestService, self.base.BaseService):
        pass

      # Register a class class, just for fun
      self.base.BaseCompute.register(Foo.TestService)(TestService_base)

      self.assertIn(Foo.TestService.__module__ + '.' + \
                    Foo.TestService.__qualname__,
                    self.base.services)

      with self.assertRaises(self.base.AlreadyRegisteredException,
                            msg='Compute command "car" does not have a service '
                                'implementation "car_service"'):
        self.base.BaseCompute.register(Foo.TestService)(lambda x: 1)

  def test_getattr(self):
    class Foo(self.base.BaseCompute):
      def bar_service(self):
        pass

    foo = Foo()
    foo.bar
    with self.assertRaises(AttributeError):
      foo.car


class TestUnitTests(TestCase):
  def setUp(self):
    from terra.compute import base
    self.base = base

  def last_test_registered_services(self):
    self.assertFalse(
      self.base.services,
      msg="If you are seeing this, one of the other unit tests has "
      "registered a terra service. This side effect should be "
      "prevented by mocking out the terra.compute.base.services dict. "
      "Otherwise unit tests can interfere with each other.")
