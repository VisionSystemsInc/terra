from unittest import TestCase as TestCaseOriginal


class TestCase(TestCaseOriginal):
  _setup_class_once = True

  @classmethod
  def setUpClass(cls):
    if TestCase._setup_class_once:
      # The logging "magic" relies on settings too much, and will result in
      # undesired errors. This disables that behavior, and leaves the logger
      # in it's initial pre-configured state. Meaning max logging to stdout
      # and a temp file. Stdout may be removed here.

      from terra.core.signals import post_settings_configured
      import terra.logger

      post_settings_configured.disconnect(terra.logger._logs.configure_logger)

      TestCase._setup_class_once = False
