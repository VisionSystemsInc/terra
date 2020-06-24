
handledExitCode = 62  # 20 + 5 + 18 + 18 + 1


class ImproperlyConfigured(Exception):
  """
  Exception for Terra is somehow improperly configured
  """


class ConfigurationWarning(Warning):
  """
  Warning that Terra may be improperly configured
  """
