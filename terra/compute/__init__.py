
DEFAULT_DB_ALIAS = 'default'


class ConnectionHandler:
  def __init__(self, databases=None):
    """
    databases is an optional dictionary of database definitions (structured
    like settings.DATABASES).
    """
    self._databases = databases
    self._connections = local()

  # @cached_property
  def databases(self):
    if self._databases is None:
      self._databases = settings.DATABASES
    if self._databases == {}:
      self._databases = {
          DEFAULT_DB_ALIAS: {
              'ENGINE': 'django.db.backends.dummy',
          },
      }
    if self._databases[DEFAULT_DB_ALIAS] == {}:
      self._databases[DEFAULT_DB_ALIAS]['ENGINE'] = 'django.db.backends.dummy'

    if DEFAULT_DB_ALIAS not in self._databases:
      raise ImproperlyConfigured(
          "You must define a '%s' database" % DEFAULT_DB_ALIAS)
    return self._databases
