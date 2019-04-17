# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be used
#        to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from threading import local
from importlib import import_module
from terra.core.utils import cached_property
from terra import settings


class ComputeHandler:
  '''
  The :class:`ComputeHandler` class gives a single entrypoint to interact with
  the compute, no matter what type it is. A standard way to call ``run``,
  etc...

  Based loosly on :class:`django.db.utils.ConnectionHandler`
  '''
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
'''ComputeHandler: The compute handler that all apps will be interfacing with.
For the most part, workflows will be interacting with :data:`compute` to
``run`` services. Easier access via ``terra.compute.compute``
'''

def load_backend(backend_name):
  '''
  Loads the compute's backend's base module, given either a fully qualified
  compute backend name, or a partial (``terra.compute.{partial}.base``)

  Parameters
  ----------
  backend_name : str
      Backend name
  '''
  try:
    return import_module(f'{backend_name}.base')
  except ImportError:
    return import_module(f'terra.compute.{backend_name}.base')


def load_service(name_or_class):
  '''
  Get (and optionally import) a service by name. Also accepts the class itself

  Parameters
  ----------
  name_or_class : :class:`str` or :class:`class`
      The service being loaded
  '''
  if not isinstance(name_or_class, str):
    name_or_class = f'{name_or_class.__module__}.{name_or_class.__name__}'
  else:
    module = name_or_class.rsplit('.', 1)[0]
    import_module(module)
  return compute.services[name_or_class]
