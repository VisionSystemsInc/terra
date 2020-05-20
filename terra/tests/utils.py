import os
from unittest import mock

from vsi.test.utils import (
  TestCase, make_traceback
)

from terra import settings


__all__ = ["TestCase", "make_traceback"]


class TestSettingsUnconfiguredCase(TestCase):
  def setUp(self):
    # Useful for tests that set this
    self.patches.append(mock.patch.dict(os.environ,
                                        {'TERRA_SETTINGS_FILE': ""}))
    # Use settings
    self.patches.append(mock.patch.object(settings, '_wrapped', None))
    super().setUp()


class TestSettingsConfiguredCase(TestSettingsUnconfiguredCase):
  def setUp(self):
    super().setUp()
    settings.configure({})
