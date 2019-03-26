
from terra.compute.utils import compute

try:
  from _terra import *
except ImportError:
  pass

__all__ = ['compute']
