from terra.core.settings import LazySettings

try:
  from _terra import *  # noqa
except ImportError:
  pass

settings = LazySettings()
'''LazySettings: The setting object to use through out all of terra'''