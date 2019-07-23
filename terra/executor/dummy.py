from concurrent.futures import Future, Executor
from threading import Lock

from terra.logger import getLogger
logger = getLogger(__name__)


class DummyExecutor(Executor):
  """
  Executor that does the nothin, just logs what would happen.
  """

  def __init__(self, *arg, **kwargs):
    self._shutdown = False
    self._shutdown_lock = Lock()

  def submit(self, fn, *args, **kwargs):
    with self._shutdown_lock:
      if self._shutdown:
        raise RuntimeError('cannot schedule new futures after shutdown')

      f = Future()
      logger.info(f'Run function: {fn}')
      logger.info(f'With args: {args}')
      logger.info(f'With kwargs: {kwargs}')
      f.set_result(None)
      return f

  def shutdown(self, wait=True):
    with self._shutdown_lock:
      self._shutdown = True
