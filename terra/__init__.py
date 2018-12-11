from terra.core.settings import LazySettings

try:
  from _terra import *  # noqa
except ImportError:
  pass

settings = LazySettings()
