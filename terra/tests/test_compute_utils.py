from unittest import mock
import warnings

from terra import settings
from .utils import TestCase
import terra.compute.utils as utils
import terra.compute.dummy
import terra.compute.docker
import terra.compute.base


class Compute(terra.compute.dummy.Compute):
  pass


class Service:
  pass


@Compute.register(Service)
class Service_test:
  pass


class Service2:
  pass


@terra.compute.base.BaseCompute.register(Service2)
class Service2_test:
  pass


# I am purposefully showing multiple ways to mock _wrapped for demonstration
# purposes


patches = []


# Module scope patch
def setUpModule():
  patches.append(mock.patch.object(settings, '_wrapped', None))
  patches.append(mock.patch.object(terra.compute.base, 'services', {}))
  for patch in patches:
    patch.start()
  settings.configure({'compute': {'arch': Compute.__module__}})


def tearDownModule():
  for patch in patches:
    patch.stop()


class TestUtils(TestCase):
  def test_compute_handler_from_settings(self):
    self.assertIsInstance(utils.ComputeHandler()._connection, Compute)

  # Function scope patch
  @mock.patch.object(settings, '_wrapped', None)
  def test_compute_handler_from_override(self):
    settings.configure({})
    self.assertIsInstance(utils.ComputeHandler()._connection,
                          terra.compute.dummy.Compute)
    self.assertIsInstance(utils.ComputeHandler(
      Compute.__module__)._connection, Compute)

  def test_compute_handler_short_name(self):
    # context manager scope patch
    with mock.patch.object(settings, '_wrapped', None),
        warnings.catch_warnings():
      settings.configure({'compute': {'arch': 'docker'}})
      warnings.simplefilter('ignore')  # Suppress imp cause by docker warnings
      self.assertIsInstance(utils.ComputeHandler()._connection,
                            terra.compute.docker.Compute)

  def test_get_default_service(self):
    self.assertIs(utils.get_default_service_class(Compute), Service)

  def test_load_service_by_instance(self):
    service = Service()
    self.assertIs(utils.load_service(service), service)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_by_class(self):
    self.assertIsInstance(utils.load_service(Service),
                          Service_test)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_by_str(self):
    self.assertIsInstance(utils.load_service(Service.__module__ + '.Service'),
                          Service_test)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_by_str_using_default_implementation(self):
    self.assertIsInstance(utils.load_service(Service.__module__ + '.Service2'),
                          Service)
