import os
from inspect import isclass
from functools import partial


class BaseService:
  env = os.environ

  def pre_run(self):
    pass

  def post_run(self):
    pass


class DSMService(BaseService):
  name = "dsm"


class ViewAngleRetrieval(BaseService):
  name = "ViewAngleRetrieval"


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

  @property
  def register(cls):
    return partial(cls._register, services=cls.services)


class BaseCompute(metaclass=MetaCompute):
  ''' Base Computing Service Model
  '''

  # The actual register service decorator
  @classmethod
  def _register(cls, service, services):
    if service.name in services:
      raise(AlreadyRegisteredException(f'Service {service.name} already '
                                       'registered'))
    services[service.name] = service
    return service

  def create(self):
    pass

  def start(self):
    pass

  def run(self):
    self.create()
    self.start()

  def stop(self):
    pass

  def remove(self):
    pass
