from unittest import mock

from terra import settings
from .utils import TestCase


class TestSomething(TestCase):
  def setUp(self):
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    super().setUp()
    settings.configure({})

  def test_something(self):
    self.assertTrue(1)
