'''
Terra in an infrastructure with the purpose of running algorithms in a compute
architecture agnostic way. The goal is, once an algorithm (app) is setup, the
same algorithm can be deployed on multiple compute arches

.. envvar:: TERRA_UNITTEST

   A environment variable that is ``1`` when running unit tests.
'''

from terra.core.settings import settings

settings = settings
'''terra.core.settings.Settings: The settings object easily accessible from all
of terra and any terra app
'''

try:
  from . import _terra
except ImportError:
  pass

__all__ = ['settings', '_terra']
