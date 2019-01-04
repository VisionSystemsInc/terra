import os

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

from functools import partial

class AlreadyRegisteredException(Exception):
  pass

# Define a class level property that is a different dictionary for every child
# class. The reason for this is so that every Compute model has a separate
# registered services list, but I don't want to repeat this identical code in
# every child
class MetaCompute(type):
  def __new__(mc1, name, bases, nmspc):
    nmspc.update({'services': MetaCompute.services})
    return super(MetaCompute, mc1).__new__(mc1, name, bases, nmspc)

  @property
  def services(cls):
    # Might as well use python's mangling pattern
    try:
      name = '_'+cls.__name__+'__services'
    except AttributeError:
      # For the case where cls is an instance
      name = '_'+cls.__class__.__name__+'__services'
    # If the var isn't already defined
    if not hasattr(cls, name):
      # Set to an empty dict
      setattr(cls, name, {})
    return getattr(cls, name)

  @services.setter
  def services(cls, val):
    try:
      name = '_'+cls.__name__+'__services'
    except AttributeError:
      name = '_'+cls.__class__.__name__+'__services'

    setattr(cls, name, val)

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
