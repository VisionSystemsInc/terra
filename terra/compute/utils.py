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

from importlib import import_module
from terra.core.utils import Handler
from terra import settings
from terra.compute.base import services as compute_services
from terra.logger import getLogger
logger = getLogger(__name__)


class ComputeHandler(Handler):
  '''
  The :class:`ComputeHandler` class gives a single entrypoint to interact with
  the compute architecture, no matter what arch type it is. A standard way to
  call ``run``, etc...
  '''

  def _connect_backend(self):
    '''
    Loads the compute's backend's base module, given either a fully qualified
    compute backend name, or a partial (``terra.compute.{partial}``), and
    then returns a connection to the backend

    A Backend should have two classes defined:

    * ``Compute`` based off of :class:`terra.compute.base.BaseCompute`
    * ``Service`` based off of :class:`terra.compute.base.BaseService`

    Parameters
    ----------
    self._overrite_type : :class:`str`, optional
        If not ``None``, override the name of the backend to load.
    '''

    backend_name = self._overrite_type

    if backend_name is None:
      backend_name = settings.compute.arch
    if not backend_name:
      backend_name = 'terra.compute.dummy'

    try:
      module = import_module(f'{backend_name}')
    except ImportError:
      module = import_module(f'terra.compute.{backend_name}')

    return module.Compute()


compute = ComputeHandler()
'''ComputeHandler: The compute handler that all apps will be interfacing with.
For the most part, workflows will be interacting with :data:`compute` to
``run`` services. Easier access via ``terra.compute.compute``
'''


def get_default_service(cls):
  '''
  Gets a compute class' default Service class from the class object.

  Arguments
  ---------
  cls : type
      The compute class whose service class you want

  Since computes are name ``Compute`` in the base module, the class ``Service``
  should be defined in the same file. This will return that ``Service`` class
  '''
  module = import_module(f'{cls.__module__}')
  return module.Service


def load_service(name_or_class):
  '''
  Get (and optionally import) a service by name. Also accepts the class itself
  or an instance of a class.

  Parameters
  ----------
  name_or_class : :class:`str` or :class:`class`
      The service being loaded

  Returns
  -------
    instance
        Instead of the class specified. If ``name_or_class`` was already an
        instance, the same instance is returned
  '''

  if not isinstance(name_or_class, str):
    # If already instance, return it
    if not isinstance(name_or_class, type):
      return name_or_class
    name_or_class = f'{name_or_class.__module__}.{name_or_class.__name__}'
  else:
    module = name_or_class.rsplit('.', 1)[0]
    import_module(module)

  try:
    services = compute_services[name_or_class]
  except KeyError:
    logger.fatal(f'{name_or_class} is not registered')
    raise

  cls = type(compute._connection)

  if cls not in services:
    logger.info(f'Using default {cls} compute handler for {name_or_class}')
    return get_default_service(cls)

  return services[cls]()
