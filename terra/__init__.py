from terra.core.settings import settings

try:
  from _terra import *
except ImportError:
  pass

__all__ = ['settings']
