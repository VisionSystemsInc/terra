from unittest import mock
import warnings
import inspect

from terra import settings
from .utils import TestCase
import terra.compute.utils as utils
import terra.compute.dummy
import terra.compute.docker
import terra.compute.base


# A test compute based off of dummy, but not dummy. These two classes turn this
# test into an official terra compute definition
class Compute(terra.compute.dummy.Compute):
  pass


class Service:
  pass


class Service_test:
  pass


class Service2:
  pass


class Service2_test:
  pass


# I am purposefully showing multiple ways to mock _wrapped for demonstration
# purposes
class TestComputeUtilsCase(TestCase):
  def setUp(self):
    # Use setting
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    # For registering a service
    self.patches.append(mock.patch.dict(terra.compute.base.services,
                                        clear=True))
    super().setUp()
    # Register this Compute
    settings.configure({'compute': {'arch': Compute.__module__}})

    # Manually register without using decorator
    Compute.register(Service)(Service_test)
    # Manually register against base compute. Normally this is never done, but
    # done for some core case tests below
    terra.compute.base.BaseCompute.register(Service2)(Service2_test)


class TestUtils(TestComputeUtilsCase):
  def test_compute_handler_from_settings(self):
    # Test handler working
    self.assertIsInstance(utils.ComputeHandler()._connection, Compute)

  # I don't want setUp's configure for this test
  @mock.patch.object(settings, '_wrapped', None)
  def test_compute_handler_from_override(self):
    settings.configure({})
    self.assertIsInstance(utils.ComputeHandler()._connection,
                          terra.compute.dummy.Compute)
    self.assertIsInstance(
        utils.ComputeHandler(Compute.__module__)._connection, Compute)

  # I don't want setUp's configure for this test
  @mock.patch.object(settings, '_wrapped', None)
  def test_compute_handler_short_name(self):
    # Since the "docker" library is installed, this test actually imports
    # docker before importing the real docker Compute, hence the warning.
    settings.configure({'compute': {'arch': 'docker'}})
    # Suppress imp warnings caused by docker
    with warnings.catch_warnings():
      warnings.simplefilter('ignore')
      # Make sure it worked
      self.assertIsInstance(utils.ComputeHandler()._connection,
                            terra.compute.docker.Compute)

  def test_get_default_service(self):
    # Make sure service definition works too
    self.assertIs(utils.get_default_service_class(Compute), Service)

  def test_load_service_by_instance(self):
    service = Service()
    self.assertIs(utils.load_service(service), service)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_by_class(self):
    from terra.compute.base import services as compute_services
    self.assertIsInstance(utils.load_service(Service), Service_test)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_by_str(self):
    self.assertIsInstance(utils.load_service(Service.__module__ + '.Service'),
                          Service_test)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_by_str_using_default_implementation(self):
    self.assertIsInstance(utils.load_service(Service.__module__ + '.Service2'),
                          Service)

  @mock.patch.dict(utils.compute.__dict__, _connection=Compute())
  def test_load_service_unregistered(self):
    with self.assertRaises(KeyError), self.assertLogs(utils.__name__) as log:
      utils.load_service(__name__)

    self.assertIn(f'{__name__} is not registered', str(log.output))


class TestComputeHandler(TestComputeUtilsCase):
  @mock.patch.object(settings, '_wrapped', None)
  def test_compute_handler(self):
    settings.configure({'compute': {'arch': 'terra.compute.dummy'}})
    test_compute = utils.ComputeHandler()
    self.assertIsInstance(test_compute._connection,
                          terra.compute.dummy.Compute)

  # Make sure this can be run twice
  test_compute_handler2 = test_compute_handler
