import os
from unittest import mock

from terra.compute import base
from .utils import TestCase


class TestServiceBase(TestCase):

  @mock.patch.dict(os.environ, {'FOO': "BAR"})
  def test_env(self):
    service = base.BaseService()
    service.env['BAR'] = 'foo'
    self.assertEqual(service.env['FOO'], 'BAR')
    self.assertEqual(service.env['BAR'], 'foo')
    self.assertNotIn("BAR", os.environ)

  def test_volumes(self):
    service = base.BaseService()
    service.add_volume("/local", "/remote")
    self.assertIn(("/local", "/remote"), service.volumes)


class TestService(base.BaseService):
  def pre_run(self):
    pass
