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

class cached_property:
  """
  Decorator that converts a method with a single self argument into a
  property cached on the instance.

  Based off of django

  Parameters
  ----------
  func : func
      The function being wrapped
  name : :class:`str`, optional
      When not used as a decorator, allows you to make cached properties of
      other methods. (e.g.
      ``url = cached_property(get_absolute_url, name='url')``)
  """

  def __init__(self, func, name=None):
    self.func = func
    self.__doc__ = getattr(func, '__doc__')
    self.name = name or func.__name__

  def __get__(self, instance, cls=None):
    """
    Call the function and puts the return value in ``instance.__dict__`` so
    that subsequent attribute access on the instance returns the cached value
    instead of calling :func:`__get__` again.
    """
    if instance is None:
      return self
    res = instance.__dict__[self.name] = self.func(instance)
    return res


class Handler:
  '''
  The :class:`Handler` is a generic handler class for abstracting specific
  type of class and the base class, essentially letting you to make calls on a
  "base" class easily, without any complications.

  Based loosly on :class:`django.db.utils.ConnectionHandler`
  '''
  def __init__(self, override_type=None):
    self._overrite_type = override_type

  def _connect_backend(self):
    '''
    Overload this function in children classes
    '''
    if self._overrite_type:
      _type = self._overrite_type
    else:
      _type = int
    return _type()

  @cached_property
  def _connection(self):
    return self._connect_backend()

  def __getattr__(self, name):
    return getattr(self._connection, name)

  def __setattr__(self, name, value):
    if name in ('_overrite_type'):
      return super().__setattr__(name, value)
    return setattr(self._connection, name, value)

  def __delattr__(self, name):
    return delattr(self._connection, name)

  # Incase this needs multiple computes simultaneously...

  # def __getitem__(self, key):
  #   if not self._connection:
  #     backend = load_backend(self.compute.arch)
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
    if hasattr(self._connection, 'close'):
      self._connection.close()
