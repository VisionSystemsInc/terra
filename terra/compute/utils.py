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
from terra.core.utils import Handler
from terra import settings


class ComputeHandler(Handler):
  '''
  The :class:`ComputeHandler` class gives a single entrypoint to interact with
  the compute architecture, no matter what arch type it is. A standard way to
  call ``run``, etc...
  '''

  def _connect_backend(self):
    '''
    Loads the compute's backend's base module, given either a fully qualified
    compute backend name, or a partial (``terra.compute.{partial}.base``), and
    then returns a connection to the backend

    Parameters
    ----------
    self._overrite_type : :class:`str`, optional
        If not ``None``, override the name of the backend to load.
    '''

    backend_name = self._overrite_type

    if backend_name is None:
      backend_name = settings.compute.arch
    if backend_name == {}:
      backend_name = 'terra.compute.dummy'

    try:
      module = import_module(f'{backend_name}.base')
    except ImportError:
      module = import_module(f'terra.compute.{backend_name}.base')

    return module.Compute()
compute = ComputeHandler()
'''ComputeHandler: The compute handler that all apps will be interfacing with.
For the most part, workflows will be interacting with :data:`compute` to
``run`` services. Easier access via ``terra.compute.compute``
'''

class ExecutorHandler(Handler):
  '''
  The :class:`ComputeHandler` class gives a single entrypoint to interact with
  the ``concurrent.futures`` executor.
  '''

  def _connect_backend(self):
    '''
    Loads the compute's backend's base module, given either a fully qualified
    compute backend name, or a partial (``terra.compute.{partial}.base``), and
    then returns a connection to the backend

    Parameters
    ----------
    self._overrite_type : :class:`str`, optional
        If not ``None``, override the name of the backend to load.
    '''

    backend_name = self._overrite_type

    if backend_name is None:
      backend_name = settings.executor.type
    if backend_name == {}:
      backend_name = 'terra.compute.dummy'

    if backend_name == "ThreadPoolExecutor":
      import concurrent.futures
      return concurrent.futures.ThreadPoolExecutor
    elif backend_name == "ProcessPoolExecutor":
      import concurrent.futures
      return concurrent.futures.ProcessPoolExecutor
    elif backend_name == "CeleryExecutor":
      import celery_executor.executors
      return celery_executor.executors.CeleryExecutor
    else:
      module_name = backend_name.rsplit('.', 1)
      module = import_module(f'{module_name[0]}')
      return getattr(module, module_name[1])
Executor = ExecutorHandler()
'''ExecutorHandler: The executor handler that all services will be interfacing
with when running parallel computation tasks.
'''

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
