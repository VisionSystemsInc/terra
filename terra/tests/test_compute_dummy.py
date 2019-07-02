import os
from unittest import mock

from terra import settings
from terra.compute import base
from terra.compute import dummy
from .utils import TestCase


# Test Dummy
class TestServiceManual(dummy.BaseService):
  # These implementations aren't actually even needed with assertLogs, however
  # I'll leave them here as future examples
  def __init__(self):
    super().__init__()
    self.a = 11

  def pre_run(self):
    super().pre_run()
    self.b = 22

  def post_run(self):
    super().post_run()
    self.c = 33


@dummy.Compute.register(TestServiceManual)
class TestServiceManual_dummy(TestServiceManual, dummy.Service):
  def __init__(self):
    super().__init__()
    self.d = 44


# Redundant tests left as implementation examples
class TestDummyManual(TestCase):
  def test_registry(self):
    self.assertIn(TestService.__module__ + '.TestService',
                  base.services)

  def test_manual_service(self):
    dummyCompute = dummy.Compute()
    foo = TestServiceManual_dummy()

    dummyCompute.run(foo)
    self.assertEqual(foo.a, 11)
    self.assertEqual(foo.b, 22)
    self.assertEqual(foo.c, 33)
    self.assertEqual(foo.d, 44)


class TestService(base.BaseService):
  pass


# Normally you don't register to the base
@base.BaseCompute.register(TestService)
class TestService_base(TestService, base.BaseService):
  pass  # No needs to register dummy even. Use default


class TestServiceDummy(TestCase):
  test_service_name = TestService.__module__ + '.TestService'

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.dummyCompute = dummy.Compute()

  @mock.patch.object(settings, '_wrapped', None)
  def test_run(self):
    settings.configure({})

    with self.assertLogs(dummy.__name__, level="INFO") as cm:
      self.dummyCompute.run(self.test_service_name)

    run = [
      'INFO:terra.compute.dummy:Run:' in o for o in cm.output].index(True)
    pre_run = [
      'INFO:terra.compute.dummy:Pre run:' in o for o in cm.output].index(True)
    create = [
      'INFO:terra.compute.dummy:Create:' in o for o in cm.output].index(True)
    start = [
      'INFO:terra.compute.dummy:Start:' in o for o in cm.output].index(True)
    post_run = [
      'INFO:terra.compute.dummy:Post run:' in o for o in cm.output].index(True)

    self.assertLess(run, pre_run)
    self.assertLess(pre_run, create)
    self.assertLess(create, start)
    self.assertLess(start, post_run)

  @mock.patch.object(settings, '_wrapped', None)
  def test_phases(self):
    settings.configure({})

    for phase in ['create', 'start', 'stop', 'remove']:
      with self.assertLogs(dummy.__name__, level="INFO") as cm:
        getattr(self.dummyCompute, phase)(self.test_service_name)
      self.assertTrue(any('INFO:terra.compute.dummy:{}:'.format(
        phase.capitalize()) in o for o in cm.output))
