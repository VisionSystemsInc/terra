import os
import logging
import concurrent.futures
from importlib import import_module

from terra import settings
from terra.core.utils import ClassHandler
import terra.logger


class ExecutorHandler(ClassHandler):
  '''
  The :class:`ExecutorHandler` class gives a single entrypoint to interact with
  the ``concurrent.futures`` executor class.
  '''

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
      return {}
    return self._connection.configuration_map(service_info)

  def reconfigure_logger(self, logging_handler):
    # The default logging handler is a StreamHandler. This will reconfigure the
    # Stream handler, should
    log_file = os.path.join(settings.processing_dir,
                            terra.logger._logs.default_log_prefix)

    # if not os.path.samefile(log_file, self._log_file.name):
    if log_file != self._log_file.name:
      os.makedirs(settings.processing_dir, exist_ok=True)
      self._log_file.close()
      self._log_file = open(log_file, 'a')

  def configure_logger(self):
    # ThreadPoolExecutor will work just fine with a normal StreamHandler

    try:
      self._configure_logger()
      # In CeleryPoolExecutor, use the Celery logger.
      # Use this to determine if main process or just a worker?
      # https://stackoverflow.com/a/45022530/4166604
      # Use JUST_IS_CELERY_WORKER
    except AttributeError:
      # Setup log file for use in configure
      self._log_file = os.path.join(settings.processing_dir,
                                    terra.logger._logs.default_log_prefix)
      os.makedirs(settings.processing_dir, exist_ok=True)
      self._log_file = open(self._log_file, 'a')

      self._logging_handler = logging.StreamHandler(stream=self._log_file)
      return self._logging_handler

      # TODO: ProcessPool - Log server


Executor = ExecutorHandler()
'''ExecutorHandler: The executor handler that all services will be interfacing
with when running parallel computation tasks.
'''
