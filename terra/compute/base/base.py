import os
from inspect import isclass
from functools import partial
from copy import copy

class BaseService:
  env = copy(os.environ)

  def pre_run(self):
    pass

  def post_run(self):
    pass


class AlreadyRegisteredException(Exception):
  pass


class MetaCompute(type):
  # Define a class level property that is a different dictionary for every child
  # class. The reason for this is so that every Compute model has a separate
  # registered services list, but I don't want to repeat this identical code in
  # every child

  def __new__(mc1, name, bases, nmspc):
    nmspc.update({'services': MetaCompute.services, '_services': {}})
    return super(MetaCompute, mc1).__new__(mc1, name, bases, nmspc)

  @property
  def services(cls):
    if not isclass(cls):
      cls = type(cls)
    return cls._services

  @services.setter
  def services(cls, val):
    if not isclass(cls):
      cls = type(cls)
    cls._services = val

  # Using a metaclass property was important for getting the right services
  # dict, otherwise BaseCompute. A metaclass property is defined every time the
  # class inherits, so the last inheritance child will get services set for it,
  # and the right services will be used, instead of the BaseCompute's services.
  # The ``register`` decorator now takes one argument,
  # the Service class (identifier) being registered against
  @property
  def register(cls):
    ''' Register a function for a particular service using a specific compute
    '''
    def wrapper(fun):
      return partial(cls._register,
                     service_name=f'{fun.__module__}.{fun.__name__}',
                     services=cls.services)
    return wrapper


class BaseCompute(metaclass=MetaCompute):
  ''' Base Computing Service Model
  '''

  # The actual register service decorator. Unlike normal decorators that run
  # everytime a function is called, this is only run when a function is
  # decorated, and not when run. The end function is undecorated, resulting in
  # no need for functools.wraps
  @classmethod
  def _register(cls, service, service_name, services):
    if service_name in services:
      raise(AlreadyRegisteredException(f'Service {service_name} already '
                                       'registered'))
    services[service_name] = service
    return service

  def create(self, *args, **kwargs):
    pass

  def start(self, *args, **kwargs):
    pass

  def run(self, *args, **kwargs):
    self.create(*args, **kwargs)
    self.start(*args, **kwargs)

  def stop(self, *args, **kwargs):
    pass

  def remove(self, *args, **kwargs):
    pass
