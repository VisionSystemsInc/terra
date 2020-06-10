import os

from .utils import TestCase
from terra.tests import original_environ


class TestOtherThings(TestCase):
  def last_test_environ_change(self):
    self.assertEqual(os.environ, original_environ)
