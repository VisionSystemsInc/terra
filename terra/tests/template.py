from unittest import mock

from terra import settings
from .utils import TestCase


class TestSomething(TestCase):
  def setUp(self):
    # Create a patch so that you can configure settings without
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    super().setUp()

    # Configure all your tests with this settings
    settings.configure({})

  # Name test here
  def test_something(self):
    # Test code goes here
    self.assertTrue(1)
