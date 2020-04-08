import os
import json

from terra import settings
import terra.compute.utils
from terra.executor import Executor
from terra.logger import getLogger
logger = getLogger(__name__)


class ServiceRunFailed(Exception):
  ''' Exception thrown when a service runner returns non-zero
  '''


class BaseService:
  '''
  The base class for all Terra Service definitions

  ``super().__init__ should`` be called when inheriting a :class:`BaseService`
  class's ``__init__``

  Service definitions can define a ``pre_{command}`` and ``post_{command}``
  function that will be called before and after a ``{command}Service`` call,
  if they exist
  '''

  def __init__(self):
    self.env = os.environ.copy()
    self.volumes = []
    ''' A copy of the processes environment variables local to a service '''

  def _validate_volume(self, local, remote,
                       check_remote=True,
                       local_must_exist=False):
    '''
    Validate volume inputs. Raise a :class:`ValueError` under any of the
    following conditions:

    - ``local`` is empty or None
    - ``check_remote`` is True and ``remote`` is empty or None
    - ``local_must_exist`` is True and ``local`` file/folder does not exist

    Raises
    ------
    ValueError
      see conditions above

    '''

    if not local:
      raise ValueError('local file/folder must be specified')
    elif check_remote and not remote:
      raise ValueError('remote file/folder must be specified')
    elif local_must_exist and not os.path.exists(local):
      raise ValueError('local file/folder does not exist {}'
                       .format(local))

  def add_volume(self, local, remote, flags=None, prefix=None,
                 local_must_exist=False):
    '''
    Add a volume to the service
    '''

    self._validate_volume(local, remote, local_must_exist=local_must_exist)
    self.volumes.append((local, remote))

  def get_volume_map(self, config, service_info):
    return []

  def pre_run(self):
    '''
    A function that runs before the run service

    All service classes should implement at least ``run_service``, as this is
    the quintessential call in running a service. ``pre_run`` in
    :class:`terra.compute.base.BaseService` is mainly responsible for handling
    Executors that need a separate volume translation
    '''

    # The executor volume map is calculated on the host side, where all the
    # information is available. For example if using docker and celery, then
    # docker config need to be run to get the container volumes, and that has
    # to be run on the host machine. So this is calculated here.
    settings.executor_volume_map = Executor.configuration_map(self)
    logger.critical(settings.executor_volume_map)


  def post_run(self):
    pass


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
    implementation = name + '_service'
    # Default implementation caller

    try:
      # super hasattr
      self.__getattribute__(implementation)
    except AttributeError:
      raise AttributeError(f'Compute command "{name}" does not have a service '
                           f'implementation "{implementation}"') from None

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

  def run_service(self, *args, **kwargs):
    '''
    Place holder for code to run an instance in the compute. Runs
    ``create`` and then runs and returns ``start`` by default.
    '''

    self.create(*args, **kwargs)
    return self.start(*args, **kwargs)

  def configuration_map_service(self, service_info):
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
