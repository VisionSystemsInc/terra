from threading import local
from importlib import import_module
from terra.core.utils import cached_property
from terra import settings


class ComputeHandler:
  def __init__(self, compute=None):
    """
    databases is an optional dictionary of compute definitions (structured
    like settings.settings.compute).
    """
    self._compute = compute
    # self._connections = local()
    self._connection = None

  @cached_property
  def __compute(self):
    if self._compute is None:
      self._compute = settings.compute
    if self._compute == {}:
      self._compute = {'type': 'terra.compute.dummy'}

    return self._compute

  def __get_connection(self):
    if not self._connection:
      backend = load_backend(self.__compute.type)
      self._connection = backend.Compute()
    return self._connection

  def __getattr__(self, name):
    return getattr(self.__get_connection(), name)

  def __setattr__(self, name, value):
    if name in ('_connection', '_compute'):
      return super().__setattr__(name, value)
    return setattr(self.__get_connection(), name, value)

  def __delattr__(self, name):
    return delattr(self.__get_connection(), name)

  # Incase this needs multiple computes simultaneously...

  # def __getitem__(self, key):
  #   if not self._connection:
  #     backend = load_backend(self.compute.type)
  #     self._connection = backend.Compute()
  #   return getattr(self._connection, key)
  #   # self.ensure_defaults(alias)
  #   # self.prepare_test_settings(alias)
  #   # db = self.databases[alias]
  #   # backend = load_backend(db['ENGINE'])
  #   # conn = backend.DatabaseWrapper(db, alias)
  #   # setattr(self._connections, alias, conn)
  #   # return self._connection

  # def __setitem__(self, key, value):
  #   setattr(self._connection, key, value)

  # def __delitem__(self, key):
  #   delattr(self._connection, key)

  def close(self):
    if self._connection:
      self._connection.close()
compute = ComputeHandler()


def load_backend(backend_name):
  # try:
  return import_module(f'{backend_name}.base')
  # except ImportError:
  #   return import_module(f'terra.compute.{backend_name}.base')


def load_service(name_or_class):
  if not isinstance(name_or_class, str):
    name_or_class = f'{name_or_class.__module__}.{name_or_class.__name__}'
  else:
    module = name_or_class.rsplit('.', 1)[0]
    import_module(module)
  return compute.services[name_or_class]
