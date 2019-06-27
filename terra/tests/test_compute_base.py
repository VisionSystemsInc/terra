import os
from unittest import mock

from terra import settings
from terra.compute import base
from .utils import TestCase

# Registration test
class Foo:
  class TestService(base.BaseService):
    def __init__(self):
      super().__init__()
      self.a = 11
    def pre_run(self):
      self.b = 22
    def pre_run(self):
      self.c = 33


@base.BaseCompute.register(Foo.TestService)
class TestService_base(Foo.TestService, base.BaseService):
  def __init__(self):
    super().__init__()
    self.d = 44


class TestServiceBase(TestCase):

  @mock.patch.dict(os.environ, {'FOO': "BAR"})
  def test_env(self):
    service = base.BaseService()
    service.env['BAR'] = 'foo'
    self.assertEqual(service.env['FOO'], 'BAR')
    self.assertEqual(service.env['BAR'], 'foo')
    self.assertNotIn("BAR", os.environ)

  @mock.patch.object(settings, '_wrapped', None)
  def test_volumes_and_configuration_map(self):
    service = base.BaseService()
    service.add_volume("/local", "/remote")
    self.assertIn(("/local", "/remote"), service.volumes)

    # Test configuration_map
    settings.configure({})
    self.assertEqual([("/local", "/remote")],
        base.BaseCompute().configuration_map(service))

  def test_registry(self):
    self.assertIn(Foo.TestService.__module__ + '.Foo.TestService',
                  base.services)
