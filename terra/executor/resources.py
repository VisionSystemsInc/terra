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

  Internally, a resource queue uses a queue of index numbers that indexes
  ``items``, but ``get`` and ``put`` will give the feel of putting and getting
  the actual items.

  Note: ``put`` does not support adding a new item.

  Parameters
  ----------
  items : int or :term:`iterable`
      A sequence of items to represent the different resources. An integer is
      shorthand for ``range(0, items_integer)``
  repeat : :class:`int`, optional
      The numver of times you want items repeated
  '''

  def __init__(self, items, repeat=1, **kwargs):
    if isinstance(items, int):
      items = range(items)

    self.items = items

    super().__init__(len(items)*repeat, **kwargs)

    for _ in range(repeat):
      for x in range(len(items)):
        super().put(x, False)

    self.local = threading.local()

  def get(self, *args, **kwargs):
    index = super().get(*args, **kwargs)
    return self.items[index]

  def put(self, item, *args, **kwargs):
    # This has the potential to ValueError, as adding a new resource in
    # is not supported
    index = self.items.index(item)
    super().put(index, *args, **kwargs)

  def put_index(self, item, *args, **kwargs):
    super().put(item, *args, **kwargs)

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
    super().__init__(items, repeat, ctx=_default_context.get_context())

    # self.pid_ledger = multiprocessing.Array
    # self.resource_ledger = multiprocessing.Array

  def __enter__(self):
    value = super().__enter__()
    return value

  def __exit__(self, exc_type, exc_value, exc_tb):
    value = self.local.value
    super().__exit__(exc_type, exc_value, exc_tb)


class ThreadedResourceQueue(ResourceQueueMixin, ThreadingQueue):
  pass


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
