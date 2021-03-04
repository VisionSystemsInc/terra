import os
from concurrent.futures import (
  ThreadPoolExecutor, ProcessPoolExecutor, as_completed
)
from multiprocessing import Process
import platform
import time
from unittest import mock

import vsi.vendored.filelock as filelock
from vsi.tools.dir_util import is_dir_empty

from terra.tests.utils import (
  TestSettingsConfigureCase, TestCase
)
from terra.executor.resources import (
  Resource, ResourceError, test_dir, logger as resource_logger,
  ProcessLocalStorage, ThreadLocalStorage, ResourceManager
)
from terra import settings

# Cheat code: Run test 100 times, efficiently, good for looking for
# intermittent issues automatically
# TERRA_UNITTEST=1 python -c "from unittest.main import main; main(
#   module=None,
#   argv=['', '-f']+100*[
#     'terra.tests.test_executor_resources.TestResourceLock.test_items'
#   ]
# )"


def get_lock_dir(name):
  return os.path.join(settings.processing_dir, '.resource.locks',
                      platform.node(), str(os.getpid()), name)


class TestResourceCase(TestSettingsConfigureCase):
  def setUp(self):
    self.config.executor = {'type': 'SyncExecutor'}
    super().setUp()


class TestResourceSimple(TestResourceCase):
  def test_resource_registry(self):
    resource = Resource('ok', 1)
    self.assertIn(resource, Resource._resources)
    resource = None
    self.assertNotIn(resource, Resource._resources)

  def test_file_name(self):
    resource = Resource('stuff', 1)
    lock_dir = get_lock_dir('stuff')

    self.assertEqual(resource.lock_file_name(0, 0),
                     os.path.join(lock_dir, '0.0.lock'))

    self.assertEqual(resource.lock_file_name(10, 999),
                     os.path.join(lock_dir, '10.999.lock'))


class TestResourceLock(TestResourceCase):
  def test_acquire_single(self):
    lock_dir = get_lock_dir('single')
    test1 = Resource('single', 2, 1)
    test2 = Resource('single', 2, 1)
    test3 = Resource('single', 2, 1)

    lock1 = test1.acquire()
    lock2 = test1.acquire()

    # Acquiring twice, should use the cached value
    self.assertEqual(lock1, lock2)

    lock3 = test2.acquire()
    # However, using an entirely different resource instance, won't have cache
    self.assertNotEqual(lock1, lock3)

    # At this point, I should be out of resources
    with self.assertRaises(ResourceError):
      test3.acquire()

  def test_release(self):
    test = Resource('test', 1, 1)

    test.acquire()
    lock = test._local.lock
    self.assertIsNotNone(test._local.lock)
    self.assertIsNotNone(test._local.resource_id)
    self.assertIsNotNone(test._local.instance_id)

    test.release()
    self.assertNotExist(lock.lock_file)
    self.assertIsNone(test._local.lock)
    self.assertIsNone(test._local.resource_id)
    self.assertIsNone(test._local.instance_id)

  def test_dir_cleanup(self):
    resource = Resource('test', 1, 1)
    if filelock.FileLock == filelock.SoftFileLock:
      self.assertNotExist(resource.lock_dir)
    else:
      self.assertExist(resource.lock_dir, is_dir=True)
    resource.acquire()
    self.assertExist(resource.lock_dir, is_dir=True)
    lock_file = resource._local.lock.lock_file
    self.assertExist(lock_file)
    resource.release()
    self.assertNotExist(lock_file)
    self.assertNotExist(resource.lock_dir)

  def test_with_context(self):
    resource = Resource('test', 2, 1)
    with resource as r1:
      pass

    with resource as r2:
      pass

    self.assertEqual(r1, r2)

  def test_repeats(self):
    repeat1 = Resource('repeat', 2, 2)
    repeat2 = Resource('repeat', 2, 2)
    repeat3 = Resource('repeat', 2, 2)
    repeat4 = Resource('repeat', 2, 2)
    repeat5 = Resource('repeat', 2, 2)

    lock1 = repeat1.acquire()
    lock2 = repeat2.acquire()
    lock3 = repeat3.acquire()
    lock4 = repeat4.acquire()
    lock1b = repeat1.acquire()
    lock2b = repeat2.acquire()
    lock3b = repeat3.acquire()
    lock4b = repeat4.acquire()


    # Four unique names
    self.assertEqual(len({repeat1._local.lock.lock_file,
                          repeat2._local.lock.lock_file,
                          repeat3._local.lock.lock_file,
                          repeat4._local.lock.lock_file}), 4)

    self.assertEqual(lock1, lock1b)
    self.assertEqual(lock2, lock2b)
    self.assertEqual(lock3, lock3b)
    self.assertEqual(lock4, lock4b)

    with self.assertRaises(ResourceError):
      repeat5.acquire()

    self.assertEqual(lock1, 0)
    self.assertEqual(repeat1._local.instance_id, 0)
    self.assertEqual(lock2, 1)
    self.assertEqual(repeat2._local.instance_id, 0)
    self.assertEqual(lock3, 0)
    self.assertEqual(repeat3._local.instance_id, 1)
    self.assertEqual(lock4, 1)
    self.assertEqual(repeat4._local.instance_id, 1)

  def test_items(self):
    resource1 = Resource('items', ['foo', 'bar'])
    resource2 = Resource('items', ['foo', 'bar'])
    resource3 = Resource('items', ['foo', 'bar'])

    foo = resource1.acquire()
    self.assertEqual(foo, 'foo')
    self.assertEqual(foo, resource1.acquire())

    bar = resource2.acquire()
    self.assertEqual(bar, 'bar')
    self.assertEqual(bar, resource2.acquire())

    with self.assertRaises(ResourceError):
      resource3.acquire()

  def test_none(self):
    # Early version of the code used None in such a way it tripped up the logic
    # This test is to make sure that doesn't happen again.

    resource1 = Resource('none', [None, None, 1], 1)
    resource2 = Resource('none', [None, None, 1], 1)
    resource3 = Resource('none', [None, None], 1)

    n1 = resource1.acquire()
    self.assertIsNone(n1)
    # Prevent the accidental delete lock loophole, which would create a race
    # condition, if not caught
    lock1 = resource1._local.lock
    self.assertIsNone(resource1.acquire())

    n2 = resource2.acquire()
    self.assertIsNone(n2)
    # resource2 should already be acquired, make sure it's not accidentally
    # unlocking and relocking again
    lock1.release()
    self.assertIsNone(resource2.acquire())
    lock1.acquire(timeout=0)

    # two unique names
    self.assertEqual(len({resource1._local.lock.lock_file,
                          resource2._local.lock.lock_file}), 2)

    with self.assertRaises(ResourceError):
      resource3.acquire()


class TestResourceSoftLock(TestResourceLock):
  def setUp(self):
    self.patches.append(mock.patch.object(filelock, 'FileLock',
                                          filelock.SoftFileLock))
    super().setUp()

  def test_dirty_dir(self):
    lock_dir = get_lock_dir('dirty')
    os.makedirs(lock_dir, exist_ok=True)

    with self.assertLogs('terra.executor.resources', level='WARNING') as cm:
      resource_logger.warning('None')
      resource1 = Resource('dirty', 1, 1)
    self.assertEqual(len(cm.output), 1)

    with open(os.path.join(lock_dir, 'foo'), 'w') as fid:
      fid.write('ok')
    with self.assertLogs('terra.executor.resources', level='WARNING') as cm:
      resource2 = Resource('dirty', 1, 1)

    self.assertIn('is not empty. Deleting it now', cm.output[0])
    self.assertFalse(os.path.exists(resource2.lock_dir))


class TestResourceSoftLockSelection(TestResourceCase):
  # Just testing the switch to softlock mechanism works
  @mock.patch.object(filelock, 'FileLock', filelock.SoftFileLock)
  def test_no_os_hard(self):
    lock_dir = get_lock_dir('no_os_hard')
    self.assertNotExist(lock_dir)
    resource1 = Resource('no_os_hard', 1, use_softfilelock=None)
    resource2 = Resource('no_os_hard', 1, use_softfilelock=False)
    resource3 = Resource('no_os_hard', 1, use_softfilelock=True)
    self.assertNotExist(lock_dir)

    self.assertEqual(resource1.FileLock, filelock.SoftFileLock)
    self.assertEqual(resource2.FileLock, filelock.SoftFileLock)
    self.assertEqual(resource3.FileLock, filelock.SoftFileLock)

  @mock.patch.object(filelock.UnixFileLock, '_acquire',
                     lambda self: exec("raise OSError('Fake fail')"))
  @mock.patch.object(filelock.WindowsFileLock, '_acquire',
                     lambda self: exec("raise OSError('Fake fail')"))
  def test_no_dir_hard_support(self):
    self.assertFalse(test_dir(self.temp_dir.name))
    lock_dir1 = get_lock_dir('no_dir_hard1')
    lock_dir2 = get_lock_dir('no_dir_hard2')
    lock_dir3 = get_lock_dir('no_dir_hard3')

    self.assertNotExist(lock_dir1)
    self.assertNotExist(lock_dir2)
    self.assertNotExist(lock_dir3)
    resource1 = Resource('no_dir_hard1', 1, use_softfilelock=None)
    resource2 = Resource('no_dir_hard2', 1, use_softfilelock=True)
    resource3 = Resource('no_dir_hard3', 1, use_softfilelock=False)
    self.assertExist(lock_dir1, is_dir=True)
    self.assertNotExist(lock_dir2)
    self.assertNotExist(lock_dir3)

    self.assertEqual(resource1.FileLock, filelock.SoftFileLock)

  @mock.patch.object(filelock, 'FileLock',
      filelock.WindowsFileLock if os.name == 'nt' else filelock.UnixFileLock)
  def test_softlock_test(self):
    supports_hard_lock = test_dir(self.temp_dir.name)

    lock_dir1 = get_lock_dir('soft1')
    lock_dir2 = get_lock_dir('soft2')
    lock_dir3 = get_lock_dir('soft3')

    self.assertNotExist(lock_dir1)
    self.assertNotExist(lock_dir2)
    self.assertNotExist(lock_dir3)
    resource1 = Resource('soft1', 1, use_softfilelock=None)
    resource2 = Resource('soft2', 1, use_softfilelock=True)
    resource3 = Resource('soft3', 1, use_softfilelock=False)

    self.assertExist(lock_dir1, is_dir=True)
    self.assertNotExist(lock_dir2)
    self.assertNotExist(lock_dir3)
    self.assertTrue(is_dir_empty(lock_dir1))


# tearDown will auto clean this, 1) preventing inter-test name collisions and
# 2) stopping strong refs of resources from being kept around

data = {}


# Cannot be member of test case class, because testcase's _outcome cannot be
# pickled "cannot serialize '_io.TextIOWrapper' object" error somewhere in
# there
def acquire(name, i):
  # This function is meant to be called once for a worker, and has some hacks
  # to guarantee simulation of that. If you are adding another test, you
  # probably don't want to use this function, so copy it and make a similar one
  l1 = data[name].acquire()
  l2 = data[name].acquire()

  # There is a chance that the same thread/process will be reused because of
  # how concurrent.futures optimizes, but i is unique, and used to prevent
  # deleting the local storage locks, for the purpose of this test. This is
  # meant to simulate "three _different_ threads/processes"
  data[name+str(i)] = data[name]._local.lock

  # Reset "worker local storage"
  data[name]._local.lock = None
  data[name]._local.resource_id = None
  data[name]._local.instance_id = None

  return (l1, l2)

class TestResourceMulti:
  '''
  Test that Resource works
  '''

  def setUp(self):
    self.config.executor = {'type': self.name}
    super().setUp()

  def tearDown(self):
    data.clear()
    super().tearDown()

  def test_acquire(self):
    data[self.name] = Resource(self.name, 2, 1)

    futures = []
    results = []
    exceptions = 0

    with self.Executor(max_workers=3) as executor:
      for i in range(3):
        futures.append(executor.submit(acquire, self.name, i))

      for future in as_completed(futures):
        try:
          results.append(future.result())
        except ResourceError:
          exceptions += 1
    if exceptions != 1:
      import pdb; pdb.set_trace()
    self.assertEqual(exceptions, 1)

    self.assertNotEqual(results[0], results[1])
    self.assertEqual(results[0][0], results[0][1])
    self.assertEqual(results[1][0], results[1][1])

  def test_local_storage_type(self):
    resource = Resource('storage', 2, 1)
    if self.ans_multiprocess:
      self.assertIsInstance(resource._local, ProcessLocalStorage)
    else:
      self.assertIsInstance(resource._local, ThreadLocalStorage)


class TestResourceThread(TestResourceMulti,
                         TestSettingsConfigureCase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.Executor = ThreadPoolExecutor
    self.name = "ThreadPoolExecutor"

    self.ans_multiprocess = False


class TestResourceProcess(TestResourceMulti,
                          TestSettingsConfigureCase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.Executor = ProcessPoolExecutor
    self.name = "ProcessPoolExecutor"

    self.ans_multiprocess = True

  @mock.patch.object(filelock, 'FileLock', filelock.SoftFileLock)
  def test_full(self):
    lock_dir = get_lock_dir('full')
    resource = Resource('full', 1, 1)

    os.makedirs(lock_dir, exist_ok=True)
    with open(os.path.join(lock_dir, '0.0.lock'), 'w') as fid:
      fid.write(str(os.getpid()))

    with self.assertRaises(ResourceError):
      resource.acquire()

    process = Process(target=lambda: 0)
    process.start()
    dead_pid = process.pid
    process.join()

    with open(os.path.join(lock_dir, '0.0.lock'), 'w') as fid:
      fid.write(str(dead_pid))

    lock = resource.acquire()

    self.assertEqual(lock, 0)


class TestResourceManager(TestResourceCase):
  def setUp(self):
    self.patches.append(mock.patch.dict(ResourceManager.resources))
    super().setUp()

  def test_register(self):
    ResourceManager.register_resource('registered', 3, 2)
    ResourceManager.register_resource('pets', ['cat', 'dog', 'bird'], 1)

    resource = ResourceManager.get_resource('registered')
    self.assertEqual(resource.name, 'registered')
    self.assertEqual(resource.repeat, 2)
    self.assertEqual(resource.resources, range(3))

    resource = ResourceManager.get_resource('pets')
    self.assertEqual(resource.name, 'pets')
    self.assertEqual(resource.repeat, 1)
    self.assertEqual(resource.resources, ['cat', 'dog', 'bird'])

  def test_unregistered(self):
    with self.assertRaises(KeyError):
      ResourceManager.get_resource('unregisterd')


class TestStrayResources(TestCase):
  def last_test_stray_resources(self):
    self.assertDictEqual(ResourceManager.resources, {})
    self.assertSetEqual(Resource._resources, set())
