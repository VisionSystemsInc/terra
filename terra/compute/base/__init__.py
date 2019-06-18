import os
from inspect import isclass
from functools import wraps

import terra.compute.utils

class BaseService:
  '''
  The base class for all Terra Service definitions

  ``super().__init__ should`` be called when inheriting a :class:`BaseService`
  class's ``__init__``
  '''

  def __init__(self):
    self.env = os.environ.copy()
    self.volumes = []
    ''' A copy of the processes environment variables local to a service '''

  def pre_run(self, compute):
    '''
    Place holder for code to run before ``run``
    '''

  def post_run(self, compute):
    '''
    Place holder for code to run after ``run``
    '''

  def add_volume(self, local, remote):
    self.volumes.append([local, remote])


class AlreadyRegisteredException(Exception):
  '''
  Exception thrown if a function has already been registered
  '''


class BaseCompute:
  '''
  The base class for all Terra Service Compute Arches
  '''
  @classmethod
  def register(cls, service):
    '''
    Used to register a function for a particular service using a specific
    compute
    '''

    service_name = f'{service.__module__}.{service.__name__}'

    def wrapper(impl):
      if service_name not in services:
        services[service_name] = {}
      if cls in services[service_name]:
        raise(AlreadyRegisteredException(f'Service {service_name} already '
                                         'registered'))
      services[service_name][cls] = impl

      return impl
    return wrapper

  def create(self, *args, **kwargs):
    '''
    Place holder for code to create an instance in the compute
    '''

  def start(self, *args, **kwargs):
    '''
    Place holder for code to create an instance in the compute
    '''

  def run(self, *args, **kwargs):
    '''
    Place holder for code to run an instance in the compute. Runs
    :func:`create` and then :func:`start` by default
    '''

    self.create(*args, **kwargs)
    self.start(*args, **kwargs)

  def stop(self, *args, **kwargs):
    '''
    Place holder for code to stop an instance in the compute
    '''

  def remove(self, *args, **kwargs):
    '''
    Place holder for code to remove an instance from the compute
    '''

  def configuration_map(self, service_class):
    '''
    Returns the mapping of volumes from the host to the remote

    Returns
    -------
    list
        Return a list of tuple pairs [(host, remote), ... ] of the volumes
        mounted from the host to remote
    '''

    service_info = terra.compute.utils.load_service(service_class)

    return service_info.volumes


services = {}
