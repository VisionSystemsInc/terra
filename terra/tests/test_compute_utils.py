from unittest import mock
import warnings
import inspect

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
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    self.patches.append(mock.patch.dict(terra.compute.base.services,
                                        clear=True))
    super().setUp()
    settings.configure({'compute': {'arch': Compute.__module__}})

    Compute.register(Service)(Service_test)
    terra.compute.base.BaseCompute.register(Service2)(Service2_test)


class TestUtils(TestComputeUtilsCase):
  def test_compute_handler_from_settings(self):
    self.assertIsInstance(utils.ComputeHandler()._connection, Compute)

  # Function scope patch
  @mock.patch.object(settings, '_wrapped', None)
  def test_compute_handler_from_override(self):
    settings.configure({})
    self.assertIsInstance(utils.ComputeHandler()._connection,
                          terra.compute.dummy.Compute)
    self.assertIsInstance(
        utils.ComputeHandler(Compute.__module__)._connection, Compute)

  def test_compute_handler_short_name(self):
    # context manager scope patch
    with mock.patch.object(settings, '_wrapped', None), \
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

    self.assertTrue(any(f'{__name__} is not registered' in line
                        for line in log.output))


class TestComputeHandler(TestComputeUtilsCase):
  @mock.patch.object(settings, '_wrapped', None)
  def test_compute_handler(self):
    settings.configure({'compute': {'arch': 'terra.compute.dummy'}})

    test_compute = utils.ComputeHandler()

    self.assertTrue(inspect.ismethod(test_compute.run))
    self.assertIsNotNone(test_compute._connection)
    self.assertIsInstance(test_compute._connection,
                          terra.compute.dummy.Compute)

  # Make sure this can be run twice
  test_compute_handler2 = test_compute_handler
