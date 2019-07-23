from terra.core.settings import settings

try:
  from . import _terra
except ImportError:
  pass

__all__ = ['settings', '_terra']
