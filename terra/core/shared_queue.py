from multiprocessing.managers import SharedMemoryManager, SyncManager
import queue
from functools import cache

from terra import settings
from terra.executor import Executor
from .exceptions import ImproperlyConfigured

import multiprocessing.util
# https://docs.python.org/3.14/library/logging.handlers.html#logging.handlers.QueueHandler
# This works for python 3.10 - 3.14
multiprocessing.util.get_logger().setLevel(multiprocessing.util.DEBUG + 1)

manager = None

class TerraQueue:
  @classmethod
  @property
  @cache
  def get_queue(cls, queue_name, *args, **kwargs):
    if not settings.configured:
      raise ImproperlyConfigured('You should not be calling get_queue until '
          'after setting are configured. Queues should not be module level '
          'variables')
    match Executor.concurrency:
      case 'multiprocess':
        # manager = SharedMemoryManager(...)
        manager = SyncManager(address=..., authkey=None)
        return cls(queue_name, *args, **kwargs)
      case 'single':
        return queue.Queue(*args, **kwargs)
      case 'multithreaded':
          return threading.Queue(*args, **kwargs)
    # Starting in python 3.14
    #   cast 'multiinterpreter':
    #     import concurrent.interpreter
    #     return concurrent.interpreters.create_queue(*args, **kwargs)

    def __new__(cls, queue_name, *args, **kwargs):
       queue_name

@cache
def get_queue(queue_name, *args, **kwargs):
  return TerraQueue.get_queue(queue_name)
