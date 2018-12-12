from threading import local
from importlib import import_module
from terra.core.utils import cached_property
from terra import settings

class ConnectionHandler:
  def __init__(self, compute=None):
    """
    databases is an optional dictionary of compute definitions (structured
    like settings.settings.compute).
    """
    self._compute = compute
    # self._connections = local()
    self._connection = None

  @cached_property
  def compute(self):
    if self._compute is None:
      self._compute = settings.compute
    if self._compute == {}:
      self._compute = {'type': 'terra.compute.dummy'}

    return self._compute

  def __getitem__(self, key):
    if not self._connection:
      backend = load_backend(self.compute.type)
      self._connection = backend.Compute()
    return getattr(self._connection, key)
    # self.ensure_defaults(alias)
    # self.prepare_test_settings(alias)
    # db = self.databases[alias]
    # backend = load_backend(db['ENGINE'])
    # conn = backend.DatabaseWrapper(db, alias)
    # setattr(self._connections, alias, conn)
    # return self._connection

  def __setitem__(self, key, value):
    setattr(self._connection, key, value)

  def __delitem__(self, key):
    delattr(self._connection, key)

  def close(self):
    if self._connection:
      self._connection.close()

def load_backend(backend_name):
  # try:
    return import_module(f'{backend_name}.base')
  # except ImportError:
    # return import_module(f'terra.compute.{backend_name}.base')