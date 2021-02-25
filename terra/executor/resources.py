'''
In a multithreaded or multiprocessing environment, it may become necessary to
divide up and balance a "resource" among multiple workers.

For example if you have 4 GPUs and each GPU can only handle two workers at a
time, you want to have a total of 8 workers, but at any one time, you want two
workings working on a specific GPU.

In order to balance this, a resource queue is maintained
'''

import os
from multiprocessing.queues import Queue as MultiprocessingQueue
from multiprocessing.context import _default_context
from queue import Empty, Full, Queue as ThreadingQueue
import threading

from terra import settings
from terra.executor import Executor
from terra.core.utils import cached_property

from terra.logger import getLogger
logger = getLogger(__name__)


class ResourceQueueMixin:
  '''
  Loads the executor backend's base module, given either a fully qualified
  compute backend name, or a partial (``terra.executor.{partial}.executor``),
  and then returns a connection to the backend

  Parameters
  ----------
  items : int or :term:`iterable`
      A sequence of items to represent the different resources. An integer is
      shorthand for ``range(0, items_integer)``
  repeat : :class:`int`, optional
      The numver of times you want items repeated
  '''

  def __enter__(self):
    try:
      self.local.value = self.get(False)
    except Empty as exc:
      raise Empty("No more resources. Either a task didn't finish and clean up, or too many workers are running") from exc

    return self.local.value

  def __exit__(self, exc_type, exc_value, exc_tb):
    try:
      self.put(self.local.value, False)
    except Full as exc:
      raise Full('Too many resources were added back') from exc


class MultiprocessResourceQueue(ResourceQueueMixin, MultiprocessingQueue):
  def __init__(self, items, repeat=1):
        # self.ledger = Queue(len(items)*repeat)
    if isinstance(items, int):
      items = range(items)

    super().__init__(len(items)*repeat, ctx=_default_context.get_context())
    for _ in range(repeat):
      for x in items:
        self.put(x, False)

    self.local = threading.local()

    # self.pid_ledger = multiprocessing.Array
    # self.resource_ledger = multiprocessing.Array

  def __enter__(self):
    value = super().__enter__()
    return value

  def __exit__(self, exc_type, exc_value, exc_tb):
    value = self.local.value
    super().__exit__(exc_type, exc_value, exc_tb)


class ThreadedResourceQueue(ResourceQueueMixin, ThreadingQueue):
  def __init__(self, items, repeat=1):
        # self.ledger = Queue(len(items)*repeat)
    if isinstance(items, int):
      items = range(items)

    super().__init__(len(items)*repeat)
    for _ in range(repeat):
      for x in items:
        self.put(x, False)

    self.local = threading.local()


class ResourceManager:
  # queues = weakref.WeakKeyDictionary()
  queues = {}
  _backend = None

  @classmethod
  def backend(cls):
    if cls._backend is None:
      if Executor._connect_backend().multiprocess:
        cls._backend = MultiprocessResourceQueue
      else:
        cls._backend = ThreadedResourceQueue
    return cls._backend

  @classmethod
  def get_resource(cls, obj):
    return cls.queues[obj]

  @classmethod
  def add_resource(cls, obj, *args, **kwargs):
    if obj in cls.queues:
      raise ValueError(f'A "{str(obj)}" queue has already been added.')
    queue = cls.backend()(*args, **kwargs)

    cls.queues[obj] = queue
