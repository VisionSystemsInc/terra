import os
import logging
import concurrent.futures
from importlib import import_module

from terra import settings
import terra.core.signals
from terra.core.utils import ClassHandler
import terra.logger


class ExecutorHandler(ClassHandler):
  '''
  The :class:`ExecutorHandler` class gives a single entrypoint to interact with
  the ``concurrent.futures`` executor class.
  '''

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def _connect_backend(self):
    '''
    Loads the executor backend's base module, given either a fully qualified
    compute backend name, or a partial (``terra.executor.{partial}.executor``),
    and then returns a connection to the backend

    Parameters
    ----------
    self._override_type : :class:`str`, optional
        If not ``None``, override the name of the backend to load.
    '''

    print('SGR - _connect_backend')

    backend_name = self._override_type

    if backend_name is None:
      backend_name = settings.executor.type

    if backend_name == "DummyExecutor":
      from terra.executor.dummy import DummyExecutor
      return DummyExecutor
    elif backend_name == "SyncExecutor":
      from terra.executor.sync import SyncExecutor
      return SyncExecutor
    elif backend_name == "ThreadPoolExecutor" or \
         backend_name == "concurrent.futures.ThreadPoolExecutor":
      from terra.executor.thread import ThreadPoolExecutor
      return terra.executor.thread.ThreadPoolExecutor
    elif backend_name == "ProcessPoolExecutor" or \
         backend_name == "concurrent.futures.ProcessPoolExecutor":
      from terra.executor.process import ProcessPoolExecutor
      return terra.executor.process.ProcessPoolExecutor
    elif backend_name == "CeleryExecutor":
      from terra.executor.celery import CeleryExecutor
      return CeleryExecutor
    else:
      module_name = backend_name.rsplit('.', 1)
      module = import_module(f'{module_name[0]}')
      return getattr(module, module_name[1])

  def configuration_map(self, service_info):
    if not hasattr(self._connection, 'configuration_map'):
      # Default behavior
      return []
    # else call the class specific implementation
    return self._connection.configuration_map(service_info)


Executor = ExecutorHandler()
'''ExecutorHandler: The executor handler that all services will be interfacing
with when running parallel computation tasks.
'''
# This Executor type is setup automatically, via
#   Handler.__getattr__ => Handler._connection => Executor._connect_backend,
# when the signal is sent. So use a lambda to delay getattr
terra.core.signals.logger_configure.connect(
    lambda *args, **kwargs: Executor.configure_logger(*args, **kwargs),
    weak=False)
terra.core.signals.logger_reconfigure.connect(
    lambda *args, **kwargs: Executor.reconfigure_logger(*args, **kwargs),
    weak=False)
