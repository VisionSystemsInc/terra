import os
from concurrent.futures import as_completed

from multiprocessing import Process
import platform
from unittest import mock

import filelock
from vsi.tools.dir_util import is_dir_empty

from terra.tests.utils import (
  TestSettingsConfigureCase, TestCase, TestThreadPoolExecutorCase
)
from terra.executor.process import ProcessPoolExecutor
from terra.executor.thread import ThreadPoolExecutor
from terra.executor.resources import (
  Resource, ResourceError, test_dir, logger as resource_logger,
  ProcessLocalStorage, ThreadLocalStorage, ResourceManager,
  atexit_resource_release
)
from terra import settings

# Cheat code: Run test 100 times, efficiently, good for looking for
# intermittent issues
# just --wrap Terra_Pipenv run env TERRA_UNITTEST=1 python -c \
#   "from unittest.main import main; main(
#     module=None,
#     argv=['', '-f']+100*[
#       'terra.tests.test_executor_resources.TestResourceLock.test_items'
#     ]
#   )"


def get_lock_dir(name):
  return os.path.join(settings.processing_dir, '.resource.locks',
                      platform.node(), str(os.getpid()), name)


class TestResourceCase(TestSettingsConfigureCase):
  def setUp(self):
    self.config.executor = {'type': 'SyncExecutor'}
    super().setUp()


class TestResourceSimple(TestResourceCase):
  def test_resource_registry(self):
    # Test that the ledger of all resources is working
    resource = Resource('ok', 1)
    self.assertIn(resource, Resource._resources)
    resource = None
    self.assertNotIn(resource, Resource._resources)

  def test_file_name(self):
    # test Resource.lock_file_name
    resource = Resource('stuff', 1)
    lock_dir = get_lock_dir('stuff')

    self.assertEqual(resource.lock_file_name(0, 0),
                     os.path.join(lock_dir, '0.0.lock'))

    self.assertEqual(resource.lock_file_name(10, 999),
                     os.path.join(lock_dir, '10.999.lock'))


class TestResourceLock(TestResourceCase):
  def test_acquire_single(self):
    # test acquiring a lock in a single thread
    test1 = Resource('single', 2, 1)
    test2 = Resource('single', 2, 1)
    test3 = Resource('single', 2, 1)

    lock1 = test1.acquire()
    lock2 = test1.acquire()

    # Acquiring twice, should use the same value
    self.assertEqual(lock1, lock2)

    lock3 = test2.acquire()
    # However, using an entirely different resource instance, won't have cache
    self.assertNotEqual(lock1, lock3)

    # At this point, I should be out of resources
    with self.assertRaises(ResourceError):
      test3.acquire()

    # cleanup warnings
    test1.release(force=True)
    test2.release(force=True)

  def test_release(self):
    # test releasing a lock in a single thread
    test = Resource('test', 1, 1)

    test.acquire()
    lock = test._local.lock
    self.assertIsNotNone(test._local.lock)
    self.assertIsNotNone(test._local.resource_id)
    self.assertIsNotNone(test._local.instance_id)

    test.release()
    # make sure file and cache is cleaned up
    self.assertNotExist(lock.lock_file)
    self.assertIsNone(test._local.lock)
    self.assertIsNone(test._local.resource_id)
    self.assertIsNone(test._local.instance_id)

  def test_force_release(self):
    test = Resource('test', 1, 1)
    test.acquire()
    test.acquire()
    test.release(force=True)
    self.assertFalse(test.is_locked)

  def test_release_on_delete(self):
    # test leftover locks are detected and cleaned up
    test = Resource('test', 1, 1)

    lock = test.acquire()

    with self.assertLogs('terra.executor.resources', level='WARNING') as cm:
      filename = test._local.lock._lock_file
      self.assertExist(filename)
      del(test)
      self.assertNotExist(filename)
    self.assertIn('A test resource was not released. Cleaning up on delete.', cm.output[0])

  def test_atexit(self):
    test1 = Resource('test1', 1, 1)
    test2 = Resource('test2', 1, 1)
    test3 = Resource('test3', 1, 1)

    lock2 = test2.acquire()
    lock3 = test3.acquire()
    lock3 = test3.acquire()

    filename2 = test2._local.lock._lock_file
    filename3 = test3._local.lock._lock_file
    self.assertExist(filename2)
    self.assertExist(filename3)
    atexit_resource_release()
    self.assertNotExist(filename2)
    self.assertNotExist(filename3)


  def test_multiple_release(self):
    test = Resource('test', 1, 1)
    self.assertFalse(test.is_locked)
    test.acquire()
    self.assertTrue(test.is_locked)
    self.assertEqual(test._local.lock._lock_counter, 1)
    test.acquire()
    self.assertTrue(test.is_locked)
    self.assertEqual(test._local.lock._lock_counter, 2)

    test.release()
    self.assertTrue(test.is_locked)
    self.assertEqual(test._local.lock._lock_counter, 1)

    test.release()
    self.assertFalse(test.is_locked)

    with self.assertRaisesRegex(ValueError,
                                "Release called with no lock acquired"):
      test.release()

  def test_dir_cleanup(self):
    # Test that empty lock dir is auto deleted
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
    # test with
    resource = Resource('test', 2, 1)

    self.assertFalse(resource.is_locked)
    with resource as r1:
      self.assertTrue(resource.is_locked)

    self.assertFalse(resource.is_locked)

    with resource as r2:
      with resource as r3:
        self.assertTrue(resource.is_locked)
        self.assertEqual(resource._local.lock._lock_counter, 2)
      self.assertTrue(resource.is_locked)
    self.assertFalse(resource.is_locked)

    self.assertEqual(r1, r2)
    self.assertEqual(r2, r3)

  def test_repeats(self):
    # test repeated resources
    repeat1 = Resource('repeat', 2, 2)
    repeat2 = Resource('repeat', 2, 2)
    repeat3 = Resource('repeat', 2, 2)
    repeat4 = Resource('repeat', 2, 2)
    repeat5 = Resource('repeat', 2, 2)

    lock1 = repeat1.acquire()
    lock2 = repeat2.acquire()
    lock3 = repeat3.acquire()
    lock4 = repeat4.acquire()

    # Four unique names
    self.assertEqual(len({repeat1._local.lock.lock_file,
                          repeat2._local.lock.lock_file,
                          repeat3._local.lock.lock_file,
                          repeat4._local.lock.lock_file}), 4)

    # reacquire, cache
    lock1b = repeat1.acquire()
    lock2b = repeat2.acquire()
    lock3b = repeat3.acquire()
    lock4b = repeat4.acquire()

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

    # Clean up warnings
    repeat1.release(force=True)
    repeat2.release(force=True)
    repeat3.release(force=True)
    repeat4.release(force=True)

  def test_items(self):
    # Test list of objects as resources
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

    # Clean up warnings
    resource1.release(force=True)
    resource2.release(force=True)

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

    # Clean up warnings
    resource1.release(force=True)
    resource2.release(force=True)


class TestResourceSoftLock(TestResourceLock):
  # test soft lock specific behaviors
  def setUp(self):
    self.patches.append(mock.patch.object(filelock, 'FileLock',
                                          filelock.SoftFileLock))
    super().setUp()

  def test_dirty_dir(self):
    # test leftover locks are detected and cleaned up
    lock_dir = get_lock_dir('dirty')
    os.makedirs(lock_dir, exist_ok=True)

    with self.assertLogs('terra.executor.resources', level='WARNING') as cm:
      resource_logger.warning('None')
      Resource('dirty', 1, 1)
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
    # test when the os doesn't support hard locks
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
    # Test dir test creating when dir does not support hard lock
    self.assertFalse(test_dir(self.temp_dir.name))
    lock_dir1 = get_lock_dir('no_dir_hard1')
    lock_dir2 = get_lock_dir('no_dir_hard2')
    lock_dir3 = get_lock_dir('no_dir_hard3')

    self.assertNotExist(lock_dir1)
    self.assertNotExist(lock_dir2)
    self.assertNotExist(lock_dir3)
    # When test would show using hard locks would fail
    resource1 = Resource('no_dir_hard1', 1, use_softfilelock=None)
    resource2 = Resource('no_dir_hard2', 1,  # noqa: F841
                         use_softfilelock=True)
    resource3 = Resource('no_dir_hard3', 1,  # noqa: F841
                         use_softfilelock=False)
    self.assertExist(lock_dir1, is_dir=True)
    self.assertNotExist(lock_dir2)
    self.assertNotExist(lock_dir3)

    self.assertEqual(resource1.FileLock, filelock.SoftFileLock)

  @mock.patch.object(filelock, 'FileLock',
                     filelock.WindowsFileLock if os.name == 'nt'
                     else filelock.UnixFileLock)
  def test_softlock_test(self):
    # Test dir test creating when os does support hard lock
    lock_dir1 = get_lock_dir('soft1')
    lock_dir2 = get_lock_dir('soft2')
    lock_dir3 = get_lock_dir('soft3')

    self.assertNotExist(lock_dir1)
    self.assertNotExist(lock_dir2)
    self.assertNotExist(lock_dir3)
    resource1 = Resource('soft1', 1, use_softfilelock=None)  # noqa: F841
    resource2 = Resource('soft2', 1, use_softfilelock=True)  # noqa: F841
    resource3 = Resource('soft3', 1, use_softfilelock=False)  # noqa: F841

    self.assertExist(lock_dir1, is_dir=True)
    self.assertNotExist(lock_dir2)
    self.assertNotExist(lock_dir3)
    self.assertTrue(is_dir_empty(lock_dir1))


# tearDown will auto clear this:
# 1) preventing inter-test name collisions
# 2) stopping strong refs of resources from being kept around

data = {}


# Cannot be member of test case class, because TestCase is not serializable.
# Somewhere in testcase's _outcome "cannot serialize '_io.TextIOWrapper'
# object" error occurs
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
  data[name + str(i)] = data[name]._local.lock

  # Reset "worker local storage"
  data[name]._local.lock = None
  data[name]._local.resource_id = None
  data[name]._local.instance_id = None

  return (l1, l2)


def simple_acquire(name):
  rv = data[name].acquire()
  # import time
  # time.sleep(0.1)
  return rv


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
    # test acquiring in parallel
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
    self.assertEqual(exceptions, 1)

    self.assertNotEqual(results[0], results[1])
    self.assertEqual(results[0][0], results[0][1])
    self.assertEqual(results[1][0], results[1][1])

  def test_multiple_executor(self):
    # unlike test_acquire, this is not trying to test the exception, so there
    # is no need to force locks to not unlock. In fact that would break this
    # test. Test to see that locks are indeed cleaned up automatically in a
    # way that means one executor after the other will not interfere with each
    # other.
    data[self.name] = Resource(self.name, 1, 1)
    for _ in range(2):
      futures = []
      with self.Executor(max_workers=1) as executor:
        futures.append(executor.submit(simple_acquire, self.name))

        for future in as_completed(futures):
          future.result()

    # double check resource was freed
    data[self.name].acquire()
    data[self.name].release()

  def test_local_storage_type(self):
    # test the types are right
    resource = Resource('storage', 2, 1)
    if self.Executor.multiprocess:
      self.assertIsInstance(resource._local, ProcessLocalStorage)
    else:
      self.assertIsInstance(resource._local, ThreadLocalStorage)


class TestResourceThread(TestResourceMulti,
                         TestSettingsConfigureCase,
                         TestThreadPoolExecutorCase):
  # Test for multithreaded case
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.Executor = ThreadPoolExecutor
    self.name = "ThreadPoolExecutor"


class TestResourceProcess(TestResourceMulti,
                          TestSettingsConfigureCase):
  # Test for multiprocess case
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.Executor = ProcessPoolExecutor
    self.name = "ProcessPoolExecutor"

  @mock.patch.object(filelock, 'FileLock', filelock.SoftFileLock)
  def test_full(self):
    # Test resource recovery after a premature termination
    lock_dir = get_lock_dir('full')
    resource = Resource('full', ['foo'], 1)

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

    self.assertEqual(lock, 'foo')
    # Test that additional calls to acquire after recovering resource, work
    self.assertEqual(lock, resource.acquire())

    # Clean up warnings
    resource.release(force=True)


class TestResourceManager(TestResourceCase):
  def setUp(self):
    self.patches.append(mock.patch.dict(ResourceManager.resources))
    super().setUp()

  def test_register(self):
    # test registration and recall work
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
    # Test getting unregistered fails
    with self.assertRaises(KeyError):
      ResourceManager.get_resource('unregistered')


class TestStrayResources(TestCase):
  def last_test_stray_resources(self):
    # Makes sure no tests leave any resources registered, possibly interfering
    # with other tests.
    self.assertDictEqual(ResourceManager.resources, {})
    # Make sure there aren't any resources left over after all the tests have
    # run. Passing this means that every test that has run has used the correct
    # mock patches or haven't kept any references around in global persistence
    self.assertSetEqual(Resource._resources, set())
