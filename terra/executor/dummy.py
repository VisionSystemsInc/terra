from concurrent.futures import Future, Executor
from threading import Lock

from terra import settings
from terra.logger import getLogger
logger = getLogger(__name__)


class DummyExecutor(Executor):
  """
  Executor that does nothing, just logs what would happen.

  Note: Don't base new executors off of this example
  """

  def __init__(self, *arg, **kwargs):
    self._shutdown = False
    self._shutdown_lock = Lock()

  def submit(self, fn, *args, **kwargs):
    '''
    '''  # Sphinx incompatible comment in original code
    with self._shutdown_lock:
      if self._shutdown:
        raise RuntimeError('cannot schedule new futures after shutdown')

      original_zone = settings.terra.zone
      # Fake the zone for the log messages
      settings.terra.zone = 'task'
      f = Future()
      logger.info(f'Run function: {fn}')
      logger.info(f'With args: {args}')
      logger.info(f'With kwargs: {kwargs}')
      f.set_result(None)
      settings.terra.zone = original_zone
      return f

  def shutdown(self, wait=True):
    with self._shutdown_lock:
      self._shutdown = True
