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

    # REVIEW could be moved out of the class and _configure_logger could be
    # a staticmethod once we can remove the hasattr check
    terra.core.signals.logger_configure.connect(self._configure_logger)
    terra.core.signals.logger_reconfigure.connect(self._reconfigure_logger)

  def _configure_logger(self, sender, **kwargs):
    print('SGR - connect configure_logger signals')

    # Register the Executor-specific configure_logger with the logger
    self.configure_logger(sender, **kwargs)

  def _reconfigure_logger(self, sender, **kwargs):
    print('SGR - connect reconfigure_logger signals')

    # Register the Executor-specific configure_logger with the logger
    self.reconfigure_logger(sender, **kwargs)

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
    elif backend_name == "ThreadPoolExecutor":
      return concurrent.futures.ThreadPoolExecutor
    elif backend_name == "ProcessPoolExecutor":
      return concurrent.futures.ProcessPoolExecutor
    elif backend_name == "CeleryExecutor":
      import terra.executor.celery
      return terra.executor.celery.CeleryExecutor
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
# when the signal is sent.
#terra.core.signals.logger_configure.connect(lambda _: Executor._configure_logger)
#terra.core.signals.logger_reconfigure.connect(lambda _: Executor._reconfigure_logger)
