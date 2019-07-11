import unittest.mock as mock

import terra.compute.utils

from .utils import TestCase


# This class need to be here, not in test_compute_utils, because it need to be
# run outside of test_compute_utils's setUpModule and tearDownModule
class TestUnitTests(TestCase):
  # Don't name this "test*" so normal discover doesn't pick it up, "last*" are
  # run last
  def last_integrity_check(self):
    # Manual mock, since setattr gets in the way, have to do this one manually
    original = object.__getattribute__(terra.compute.utils.compute,
                                       '_connect_backend')
    object.__setattr__(terra.compute.utils.compute, '_connect_backend',
                      lambda: 31)

    self.assertEqual(terra.compute.utils.compute._connection, 31,
        msg="If you are seeing this, one of the other unit tests has "
            "initialized the compute connection. The side effect should be "
            "prevented by mocking out the _connection attribute. Otherwise "
            "unit tests can interfere with each other. Add 'import traceback; "
            " traceback.print_stack()' to ComputeHandler._connect_backend")
    object.__setattr__(terra.compute.utils.compute, '_connect_backend',
                       original)
