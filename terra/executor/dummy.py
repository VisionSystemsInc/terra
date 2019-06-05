# https://stackoverflow.com/a/10436851

from concurrent.futures import Future, Executor
from threading import Lock


class DummyExecutor(Executor):

  def __init__(self, *arg, **kwargs):
    self._shutdown = False
    self._shutdownLock = Lock()

  def submit(self, fn, *args, **kwargs):
    with self._shutdownLock:
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
    with self._shutdownLock:
      self._shutdown = True


if __name__ == '__main__':

  def fnc(err):
    if err:
      raise Exception("test")
    else:
      return "ok"

  ex = DummyExecutor()
  print(ex.submit(fnc, True))
  print(ex.submit(fnc, False))
  ex.shutdown()
  ex.submit(fnc, True)  # raises exception
