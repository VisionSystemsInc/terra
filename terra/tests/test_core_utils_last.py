import unittest.mock as mock

import terra.compute.utils
from terra import settings

from .utils import TestCase


# This class need to be here, not in test_compute_utils, because it need to be
# run outside of test_compute_utils's setUpModule and tearDownModule
class TestUnitTests(TestCase):
  # Don't name this "test*" so normal discover doesn't pick it up, "last*" are
  # run last
  def last_test_connection_handler(self):
    self.assertNotIn(
        '_connection', terra.compute.utils.compute.__dict__,
        msg="If you are seeing this, one of the other unit tests has "
            "initialized the compute connection. This side effect should be "
            "prevented by mocking out the _connection attribute. Otherwise "
            "unit tests can interfere with each other. Add 'import traceback; "
            " traceback.print_stack()' to ComputeHandler._connect_backend")

  def last_test_settings(self):
    self.assertIsNone(
        settings._wrapped,
        msg="If you are seting this, one of the other unit tests has "
            "initialized the settings. This side effect should be "
            "prevented by mocking out the settings._wrapped attribute. "
            "Otherwise unit tests can interfere with each other")
