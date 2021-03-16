'''
In a multithreaded or multiprocessing environment, it may become necessary to
divide up and balance a limited "resource" among multiple workers. For example,
if you have 4 GPUs and each GPU can only handle two workers at a time, you
would have a total of 8 workers. However, while running a
:class:`terra.task.TerraTask` each worker would need to know what resource id
(i.e. which specific GPU) to use. A :class:`Resource` handles and balances this
for you in an easy-to-manage way.
'''

import os
import threading
import platform
import tempfile
import atexit
import weakref
from shutil import rmtree
import filelock

from vsi.tools.dir_util import is_dir_empty

from terra import settings
from terra.executor import Executor

from terra.logger import getLogger
logger = getLogger(__name__)


class ResourceError(Exception):
  '''
  Exception thrown when no more resources are available
  '''


class ProcessLocalStorage:
  '''
  Processor local storage class
  '''
  resource_id = None
  instance_id = None
  lock = None


class ThreadLocalStorage(ProcessLocalStorage, threading.local):
  '''
  Thread version of :class:`ProcessLocalStorage`
  '''


class Resource:
  '''
  A :class:`Resource` instance represents a set of resources that can be
  shared between multiple threads or processes on a single computer.

  This class will allocate a resource for a task to use by simply calling
  :meth:`acquire` or using a :ref:`with <python:with>` context manager.
  Multiple calls to :meth:`acquire` or using nested :ref:`with <python:with>`-s
  are ok, as it will simply use the same resource every time. For each call to
  :meth:`acquire`, an equal number of calls to :meth:`release` are required.
  For this reason, using :ref:`with <python:with>` context managers are often
  the easier way to go.

  There should be at most as many workers as resources available for a specific
  queue of workers. Because there are enough resources for every worker, the
  resource can be considered reserved for the entire time a task runs---there
  is no need to release early after a function call or a small piece of the
  task because no one is waiting for resources.

  Resources need to be registered via the :class:`ResourceManager` prior to
  creating worker threads/processes, so that they are configured correctly

  Parameters
  ----------
  resource_name: str
      A unique name of resource. Must not contain symbols incompatible with the
      filesystem
  resources : int or :term:`iterable`
      A sequence of items to represent the different resources. An integer is
      shorthand for ``range(0, items_integer)``. If objects are used for
      resources, they need to be pickleable, or else multiprocessing will fail.
  repeat : :class:`int`, optional
      The number of workers you want to be able to acquire a resource, e.g.,
      two simultaneous workers per resource.
  use_softfilelock: bool or None
      If an OS does not support hard locks, :class:`filelock.SoftFileLock` will
      be used automatically. However, even if the OS supports hard locks, some
      filesystems (especially network file systems) may not support successful
      hard locking. In these cases, hardlock support needs to be tested on a
      per directory basis. By default, ``use_softfilelock`` is set to ``None``,
      which will run :func:`test_dir` to determine if the directory can handle
      hard locking, and update ``self._use_softfilelock`` to ``True`` or
      ``False``. Setting ``use_softfilelock`` to ``True`` or ``False`` will
      bypass testing, and always use the supplied value.

  Note
  ----
  This class is based on using lock files to lock resources. Why use lock
  files? Hard-lock files are one of the few methods that are tolerant to
  unlocking after a seg fault. Given that both windows and linux support hard
  file locking, it is easy to use and makes more sense to use lock files than
  other forms of IPC to track resources and handle seg faults. Soft file
  locking is also supported, but less preferred.

  Note
  ----
  This class supports :ref:`executor`-s that use threading or multiprocessing
  to spawn workers. There is no additional effort needed to maintain this
  worker isolation. However, if a single task in a threaded executor worker
  were to spawn additional threads (a new process has a new thread too) during
  a task's execution, then :class:`Resource` would have no way of knowing that
  the new threads were part of the same worker. The same is true if a single
  task in a multiprocess executor worker were to spawn additional processes. If
  this were to ever occur, be sure to acquire the resource before spawning to
  get the intended result.
  '''

  _resources = weakref.WeakSet()

  def __init__(self, resource_name, resources, repeat=1,
               use_softfilelock=None):
    if isinstance(resources, int):
      resources = range(resources)

    self.resources = resources
    self.repeat = repeat
    self.lock_dir = os.path.join(settings.processing_dir,
                                 '.resource.locks',
                                 platform.node(),
                                 str(os.getpid()),
                                 resource_name)
    '''
    str: The directory where the lock files will be stored.

    By default, uses the ``settings.processing_dir`` to store the lock files. A
    specific lock dir represents a specific resource, and contains the pid of
    the parent process so that spawned processes will be able to communicate
    about the same resource. Also contains the hostname so that multiple host
    workers will not collide when using a common network based filesystem.
    '''

    self.name = resource_name

    # self.FileLock = filelock.FileLock # Not pickleable
    self._use_softfilelock = use_softfilelock

    # Check if I have to use SoftFileLock for specific directories
    if self._use_softfilelock is None and \
        filelock.FileLock != filelock.SoftFileLock:
      os.makedirs(self.lock_dir, exist_ok=True)
      self._use_softfilelock = not test_dir(self.lock_dir)

    # SoftLocks can only work if a file isn't left over by accident.
    if self.FileLock == filelock.SoftFileLock:
      if os.path.isdir(self.lock_dir) and not is_dir_empty(self.lock_dir):
        logger.warning(f'Lock dir "{self.lock_dir}" is not empty. Deleting it '
                       'now for soft-lock support.')
        rmtree(self.lock_dir)

    if Executor._connect_backend().multiprocess:
      self._local = ProcessLocalStorage()
    else:
      self._local = ThreadLocalStorage()

    Resource._resources.add(self)

  def lock_file_name(self, resource_index, repeat):
    return os.path.join(self.lock_dir, f'{resource_index}.{repeat}.lock')

  # If a race condition I missed happens, a master lock could take care of
  # things. Currently not needed.
  # @property
  # def master_lock(self):
  #   return self.FileLock(os.path.join(self.lock_dir, 'master.lock'))

  @property
  def FileLock(self):
    '''
    :term:`class`: The class of :attr:`filelock.FileLock` used for locks in
    :attr:`Resource.lock_dir`.

    Hard locking is better, but only works if the OS and Filesystem supports
    it. Sometimes it is necessary to use soft locking, so this property will
    always return the correct class to use.
    '''
    if self._use_softfilelock:
      return filelock.SoftFileLock
    return filelock.FileLock

  @property
  def is_locked(self):
    if self._local.lock is None:
      return False
    return self._local.lock.is_locked

  def _acquire(self, lock_file, resource_index, repeat):
    lock = self.FileLock(lock_file, 0)
    lock.acquire()
    os.write(lock._lock_file_fd, str(os.getpid()).encode())
    # If you get this far, the lock is good, so save it in the class
    self._local.lock = lock
    self._local.resource_id = resource_index
    self._local.instance_id = repeat
    return self.resources[self._local.resource_id]

  def acquire(self):
    '''
    Acquires and locks a resource. Multiple calls will return the same resource
    and increase the lock counter.

    Returns
    ----------
    :obj:`object`
        Returns the resource that is allocated to this worker

    Raises
    ------
    ResourceError
        There are no more resources available. This should not happen if the
        total number of resources and workers are equal.

        If a thread/process worker spawns additional threads/processes, then
        the resource needs to be acquired by the actual worker (in celery, this
        is called the "worker child", not to be confused with the "worker"
        parent, which is more of a manager process and thus does not need a
        resource) and then passed along to the other threads without using this
        class.
    '''
    # Reuse for life of thread/process, unless someone calls release
    if self.is_locked:
      # Increment current counter
      self._local.lock.acquire()
      return self.resources[self._local.resource_id]

    os.makedirs(self.lock_dir, exist_ok=True)
    # with self.master_lock:
    for repeat in range(self.repeat):
      for resource_index in range(len(self.resources)):
        try:
          lock_file = self.lock_file_name(resource_index, repeat)
          return self._acquire(lock_file, resource_index, repeat)
        except filelock.Timeout:
          # If softlock is used on multiprocessing, there is a chance to
          # recover resources
          if self.FileLock == filelock.SoftFileLock and \
            not isinstance(self._local, threading.local):
            with open(self.lock_file_name(resource_index, repeat), 'r') as fid:
              pid = fid.read()
            # if file is empty, it hasn't flushed, which means still running!
            if pid:
              try:
                os.kill(int(pid), 0)
              # except PermissionError:
              #   # This only happens if the pid exists, but you don't have
              #   # permissions... still, that shouldn't happen
              #   pass
              except ProcessLookupError:
                # Clean up what was probably a seg fault
                os.remove(lock_file)
                return self._acquire(lock_file, resource_index, repeat)
    raise ResourceError(f'No more resources available for "{self.name}"')

  def release(self, force=False):
    '''
    Releases a resource and unlocks the associated lock file.

    If the resource has been locked multiple times, calling :meth:`release`
    decrements the counter, and only releases when the counter reaches zero.

    Parameters
    ----------
    force: bool
        If true, the lock counter is ignored and the lock is released in every
        case.

    Raises
    ------
    ValueError
        Raised if the resource is not currently locked
    '''
    if not self.is_locked:
      raise ValueError('Release called with no lock acquired')

    if not force and self._local.lock._lock_counter > 1:
      self._local.lock.release()
      return

    # with self.master_lock:
    # Clear the local cached first, in case other threads are watching, which
    # is unlikely
    lock = self._local.lock
    self._local.lock = None
    self._local.resource_id = None
    self._local.instance_id = None

    if isinstance(lock, filelock.UnixFileLock):
      if os.path.exists(lock.lock_file):
        # Only UnixFileLock doesn't remove the file _after_ unlocking due to a
        # race condition. This can be avoided by simply removing the file
        # _before_ unlocking. Testing using lslock shows that this cleans up
        # and works exactly as expected.
        os.remove(lock.lock_file)
    lock.release(force)

    if os.path.isdir(self.lock_dir) and is_dir_empty(self.lock_dir):
      os.rmdir(self.lock_dir)

  def __enter__(self):
    return self.acquire()

  def __exit__(self, exc_type, exc_value, exc_tb):
    self.release()
    return None

  def __del__(self):
    if self.is_locked:
      logger.warning(f"A {self.name} resource was not released. Cleaning up "
                     "on delete.")
      self.release(force=True)


# class CachedResource(Resource):
#   '''
#   Like the :class:`Resource`, but instead of using normal context managers,
#   it uses `cached context managers <https://www.python.org/dev/peps/pep-0343/
#   #caching-context-managers>`_
#
#   Calls to :meth:`release` are never needed. The only time a resource needs
#   to be released is when the thread/process is ending, in which case it is
#   called automatically on delete at exit.
#   '''
#   def __exit__(self, exc_type, exc_value, exc_tb):
#      pass

#   def acquire(self):
#     '''
#     Unlike :meth:`Resource.acquire`, :class:`CachedResource` does not use a
#     counter on the lock. Instead multiple calls to acquire returns the
#     resource object.
#     '''
#     # Reuse for life of thread/process, unless someone calls release
#     if self.is_locked:
#       return self.resources[self._local.resource_id]
#     return super().acquire()

#   def __del__(self):
#     if self.is_locked:
#       self.release()

@atexit.register
def atexit_resource_release():
  '''
  Clean up all resources before python starts unloading :mod:`os` because
  then it's too late.
  '''
  for resource in Resource._resources:
    if resource.is_locked:
      resource.release(force=True)


class ResourceManager:
  '''
  A singleton class that provides global scope access to :class:`Resource`-s

  Resources need to be registered before worker threads or processes are
  created or else they will not inherit the correct resource settings.

  Example
  -------

      ResourceManager.register_resource("gpu", 2, 4)

      def run():
        with ResourceManager.get_resource("gpu") as gpu:
          print(f"I'm using gpu {gpu}")

      with ProcessPoolExecutor(max_workers=8) as executor:
        executor.submit(run)
  '''
  resources = {}

  @classmethod
  def get_resource(cls, name):
    return cls.resources[name]

  @classmethod
  # def register_resource(cls, name, cached=True, *args, **kwargs):
  def register_resource(cls, name, *args, **kwargs):
    '''
    Registers a new resource

    Resources should be registered in: ``{app}/tasks/__init__.py``. This works
    out because tasks are loaded after settings and logging are loaded, but
    before the Executor spawns workers.

    Parameters
    ----------
    name : str
        A unique name for the resource. Must not contain symbols
        incompatible with the filesystem. Simple alphanumerics suggested.
    *args
        Additional args passed to :class:`Resource` init
    **kwargs
        Additional keyword args passed to :class:`Resource` init

    Raises
    ------
    ValueError
        If a resource with that name already exists
    '''
    '''
    cached: bool
        Choose to use a cached context manager via :class:`CachedResource` over
        a normal context manager using :class:`Resource`.
    '''
    if name in cls.resources:
      raise ValueError(f'A "{name}" resource has already been added.')
    # if cached:
    #   resource = CachedResource(name, *args, **kwargs)
    # else:
    resource = Resource(name, *args, **kwargs)

    cls.resources[name] = resource


def test_dir(path):
  '''
  Test if a directory will support hard file locking.

  If the directory cannot support hard file locking, then the
  ``use_softfilelock`` needs to be set to ``True``.
  '''

  if not os.path.isdir(path):
    raise TypeError(f'Existing directory expected, instead got {path}')

  # Use unsafe method on purpose, I don't want the file precreated
  tmp_file = tempfile.mktemp(dir=path)

  lock1 = filelock.FileLock(tmp_file)
  lock2 = filelock.FileLock(tmp_file)

  # If this fails miserably, just don't even try and use soft locks
  try:
    lock1.acquire(timeout=0)

    try:
      lock2.acquire(timeout=0)
    except filelock.Timeout:
      pass
    else:
      raise Exception("No timeout exception")

    lock2.release()
    lock1.release()
  except Exception:
    return False
  finally:
    # Best effort cleanup
    try:
      lock2.release(force=True)
    except Exception:
      pass

    try:
      lock1.release(force=True)
    except Exception:
      pass

    # Best effort delete file
    try:
      os.remove(tmp_file)
    except Exception:
      pass

  return True
