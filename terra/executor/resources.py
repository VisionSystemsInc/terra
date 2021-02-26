'''
In a multithreaded or multiprocessing environment, it may become necessary to
divide up and balance a "resource" among multiple workers.

For example if you have 4 GPUs and each GPU can only handle two workers at a
time, you want to have a total of 8 workers, but at any one time, you want two
workings working on a specific GPU.

In order to balance this, a resource queue is maintained
'''

import os
# from multiprocessing.queues import Queue as MultiprocessingQueue
# from multiprocessing.context import _default_context
# from queue import Empty, Full, Queue as ThreadingQueue
import threading
import platform
import multiprocessing
from ctypes import c_int32
from shutil import rmtree
import filelock

from vsi.tools.dir_util import is_dir_empty

from terra import settings
from terra.executor import Executor
from terra.core.utils import cached_property

from terra.logger import getLogger
logger = getLogger(__name__)


class Resource:
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

  def __init__(self, resource_name, resources, repeat=1):
    if isinstance(resources, int):
      resources = range(resources)

    self.resources = resources
    self.repeat = repeat
    self.lock_dir = os.path.join(settings.processing_dir,
                                 '.resource.locks',
                                 platform.node(),
                                 str(os.getpid()),
                                 resource_name)

    self.FileLock = filelock.FileLock
    # In case I need to check if I have to use SoftFileLock for specific,
    # directories, that can go here. Currently it will use Unix/Windows if the
    # os supports it.

    if Executor._connect_backend().multiprocess:
      self._lock = type("pls", (object,), {'value': None})
    else:
      self._lock = threading.local()
    self._lock.value = None

    if self.FileLock == filelock.SoftFileLock:
      if os.path.exists(self.lock_dir):
        logger.warning(f'Lock dir "{self.lock_dir}" is not empty. Deleting it '
                      'now...')
        rmtree(self.lock_dir)

  def lock_file_name(self, resource_index, repeat):
    return os.path.join(self.lock_dir, f'{resource_index}.{repeat}.lock')

  def acquire(self):
    if not os.path.exists(self.lock_dir):
      os.makedirs(self.lock_dir)
    for repeat in range(self.repeat):
      for resource_index in range(len(self.resources)):
        try:
          lock = self.FileLock(self.lock_file_name(resource_index, repeat), 0)
          self._lock.value = (lock, self.resources[resource_index])
          return self._lock.value
        except filelock.Timeout:
          continue

    raise ValueError('No lock available')
    # logger.error('No lock available for {self.name}')
    # Attempt reclamation if SoftFileLock, else attempt timeout

  def __enter__(self):
    if self._lock.value is None:
      self._lock.value = self.acquire()

    return self._lock.value[1]

  def __exit__(self, exc_type, exc_value, exc_tb):
    pass

  def release(self):
    if self._lock.value is None:
      raise ValueError('Release called with no lock acquired')

    self._lock.value[0].release()

    if is_dir_empty(self.lock_dir):
      os.rmdir(self.lock_dir)

    # super().__init__(len(items)*repeat, **kwargs)

    # for _ in range(repeat):
    #   for x in range(len(items)):
    #     super().put(x, False)


  # def get(self, *args, **kwargs):
  #   if self._lock.value is None:
  #     index = super().get(*args, **kwargs)
  #     return self.items[index]
  #   return self._lock.value

  # def __enter__(self):
  #   try:
  #     self.local.value = self.get(False)
  #   except Empty as exc:
  #     raise Empty("No more resources. Either a task didn't finish and clean up, or too many workers are running") from exc

  #   return self.local.value

  # def __exit__(self, exc_type, exc_value, exc_tb):
  #   try:
  #     self.put(self.local.value, False)
  #   except Full as exc:
  #     raise Full('Too many resources were added back') from exc


class ResourceManager:
  resources = {}

  @classmethod
  def get_resource(cls, name):
    return cls.resources[name]

  @classmethod
  def add_resource(cls, name, *args, **kwargs):
    if name in cls.resources:
      raise ValueError(f'A "{name}" queue has already been added.')
    queue = Resource(name, *args, **kwargs)

    cls.resources[name] = queue
