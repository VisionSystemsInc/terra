import os
from unittest import mock

from terra import settings
from terra.compute import base
from .utils import TestCase


# Registration test
class Foo:
  class TestService(base.BaseService):
    pass


class TestService_base(Foo.TestService, base.BaseService):
  pass


class TestServiceBase(TestCase):
  def setUp(self):
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    self.patches.append(mock.patch.dict(base.services, clear=True))
    super().setUp()
    settings.configure({})

    base.BaseCompute.register(Foo.TestService)(TestService_base)

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
