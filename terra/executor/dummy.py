from concurrent.futures import Future, Executor
from threading import Lock


# No need for a global shutdown lock here, not multi-threaded/process


class DummyExecutor(Executor):
  """
  Executor that does the job syncronously.

  All the returned Futures will be already resolved. This executor is intended
  to be mainly used on tests or to keep internal API conformance with the
  Executor interface.

  Based on a snippet from https://stackoverflow.com/a/10436851/798575
  """

  def __init__(self, *arg, **kwargs):
    self._shutdown = False
    self._shutdown_lock = Lock()

  def submit(self, fn, *args, **kwargs):
    with self._shutdown_lock:
      if self._shutdown:
        raise RuntimeError('cannot schedule new futures after shutdown')

      f = Future()
      try:
        result = fn(*args, **kwargs)
      except BaseException as e:
        f.set_exception(e)
      else:
        f.set_result(result)

      return f

  def shutdown(self, wait=True):
    with self._shutdown_lock:
      self._shutdown = True
