import os

import terra.compute.utils


class ServiceRunFailed(Exception):
  ''' Exception thrown when a service runner returns non-zero
  '''


class BaseService:
  '''
  The base class for all Terra Service definitions

  ``super().__init__ should`` be called when inheriting a :class:`BaseService`
  class's ``__init__``

  Service dewfinitoins can define a ``pre_{command}`` and ``post_{command}``
  function that will be called before and after a ``{command}Service`` call,
  if they exist
  '''

  def __init__(self):
    self.env = os.environ.copy()
    self.volumes = []
    ''' A copy of the processes environment variables local to a service '''

  def pre_run(self):
    '''
    Place holder for code to run before ``run``
    '''

  def post_run(self):
    '''
    Place holder for code to run after ``run``
    '''

  def add_volume(self, local, remote):
    self.volumes.append((local, remote))


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

    service_name = f'{service.__module__}.{service.__qualname__}'

    def wrapper(impl):
      if service_name not in services:
        services[service_name] = {}
      if cls in services[service_name]:
        raise AlreadyRegisteredException(f'Service {service_name} already '
                                         'registered')
      services[service_name][cls] = impl

      return impl

    return wrapper

  def __getattr__(self, name):
    implementation = name + 'Service'
    # Default implementation caller

    try:
      # super hasattr
      self.__getattribute__(name + 'Service')
    except AttributeError:
      raise AttributeError(f'Compute command "{name}" does not have a service '
                           f'implementation "{implementation}"')
    else:
      def defaultCommand(self, service_class, *args, **kwargs):

        service_info = terra.compute.utils.load_service(service_class)

        # Check and call pre_ call
        pre_call = getattr(service_info, 'pre_' + name, None)
        if pre_call:
          pre_call(*args, **kwargs)

        # Call command implementation
        rv = self.__getattribute__(implementation)(
            service_info, *args, **kwargs)

        # Check and call post_ call
        post_call = getattr(service_info, 'post_' + name, None)
        if post_call:
          post_call(*args, **kwargs)

        return rv

      defaultCommand.__doc__ = f'''The {name} command for {__class__.__qualname__}

        The {name} command will call the a service's pre_{name} if it has one,
        followed by the {implementation}, and then the service's post_{name} if
        it has one.
        Calls {implementation}'''  # noqa
      defaultCommand.__name__ = name
      defaultCommand.__qualname__ = type(self).__qualname__ + '.' + name

      # bind function and return it
      return defaultCommand.__get__(self, type(self))

  def runService(self, *args, **kwargs):
    '''
    Place holder for code to run an instance in the compute. Runs
    :func:`create` and then runs and returns :func:`start` by default.
    '''

    self.create(*args, **kwargs)
    return self.start(*args, **kwargs)

  def configuration_mapService(self, service_info):
    '''
    Returns the mapping of volumes from the host to the remote

    Returns
    -------
    list
        Return a list of tuple pairs [(host, remote), ... ] of the volumes
        mounted from the host to remote
    '''

    return service_info.volumes


services = {}
