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
  TestSettingsConfiguredCase, TestSettingsUnconfiguredCase, TestCase
)
from terra.executor.resources import (
  Resource, ResourceError, test_dir, logger as resource_logger,
  ProcessLocalStorage, ThreadLocalStorage
)
from terra import settings


def get_lock_dir(name):
  return os.path.join(settings.processing_dir, '.resource.locks',
                      platform.node(), str(os.getpid()), name)


class TestResourceCase:
  def setUp(self):
    super().setUp()
    settings.configure({'executor': {"type": 'SyncExecutor'},
                        'processing_dir': self.temp_dir.name})


class TestResourceSimple(TestResourceCase, TestSettingsUnconfiguredCase):
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


class TestResourceLock(TestResourceCase, TestSettingsUnconfiguredCase):
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

  def test_dir_cleanup(self):
    resource = Resource('test', 1, 1)
    if filelock.FileLock == filelock.SoftFileLock:
      self.assertFalse(os.path.exists(resource.lock_dir))
    else:
      self.assertTrue(os.path.exists(resource.lock_dir))
    resource.acquire()
    self.assertTrue(os.path.exists(resource.lock_dir))
    resource.release()
    self.assertFalse(os.path.exists(resource.lock_dir))

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


class TestResourceSoftLock(TestResourceLock, TestSettingsUnconfiguredCase):
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


class TestResourceSoftLockSelection(TestResourceCase,
                                    TestSettingsUnconfiguredCase):
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

    # soft1 = resource1.acquire()
    # lock_file = resource1._local.lock.lock_file
    # self.assertExist(lock_file, is_dir=False)
    # resource1.release()
    # self.assertNotExist(lock_file)


data = {}


# Cannot be member of test case class, because testcase's _outcome cannot be
# pickled "cannot serialize '_io.TextIOWrapper' object" error somewhere in
# there
def acquire_delay(name):
  rv = (data[name].acquire(), data[name].acquire())
  time.sleep(0.1)
  return rv

def acquire(name):
  return (data[name].acquire(), data[name].acquire())

class TestResource:
  '''
  Test that Resource works
  '''

  def setUp(self):
    super().setUp()
    settings.configure({'executor': {"type": self.name},
                        'processing_dir': self.temp_dir.name})

  def tearDown(self):
    data.clear()
    super().tearDown()

  def test_acquire(self):
    data[self.name] = Resource(self.name, 2, 1)

    futures = []
    results = []
    exceptions = 0

    with self.Executor(max_workers=3) as executor:
      for _ in range(3):
        # Need a delay, or else a worker might be reused because of how
        # concurrent.futures optimizes, which screw up because acquire uses
        # worker local storage
        futures.append(executor.submit(acquire_delay, self.name))

      for future in as_completed(futures):
        try:
          results.append(future.result())
        except ResourceError:
          exceptions += 1
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


class TestResourceThread(TestResource,
                         TestSettingsUnconfiguredCase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.Executor = ThreadPoolExecutor
    self.name = "ThreadPoolExecutor"

    self.ans_multiprocess = False


class TestResourceProcess(TestResource,
                          TestSettingsUnconfiguredCase):
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

# class CommonResourceManager:
#   def get_resource(self):
#     return global_data['test1'].get(True)

#   def resource_queue_test(self, QueueType, Executor):
#     items = [11, 22, 33]
#     global_data['test1'] = QueueType(items)
#     futures = []
#     results = []

#     with Executor(max_workers=3) as executor:
#       for _ in range(3):
#         futures.append(executor.submit(get_resource))

#       for future in as_completed(futures):
#         results.append(future.result())

#     self.assertIn(11, results)
#     self.assertIn(22, results)
#     self.assertIn(33, results)

#     with self.assertRaises(Empty):
#       global_data['test1'].get(False)

#     # with Executor(max_workers=3) as executor:
#     #   for x in range(3):
#     #     futures.append(executor.submit(put_resource, items[x]))

#     #   for future in as_completed(futures):
#     #     future.result()

#     # with self.assertRaises(Full):
#     #   global_data['test1'].put(items[0], False)

#     # with self.assertRaises(ValueError):
#     #   global_data['test1'].put(15, False)

#     # self.assertIn(global_data['test1'].get(False), items)

#     # while not global_data['test1'].empty():
#     #   global_data['test1'].get(False)

#     # global_data['test1'].put(items[0], False)
#     # global_data['test1'].put(items[0], False)
#     # global_data['test1'].put_index(0, False)

#     # print('------------')
#     # while not global_data['test1'].empty():
#     #   global_data['test1'].get(False)
#     #   # self.assertEqual(global_data['test1'].get(False), items[0])

#     # if hasattr(global_data['test1'], 'close'):
#     #   global_data['test1'].close()
#     #   global_data['test1'].join_thread()


# class TestThreadResourceManger(TestResourceCase, CommonResourceManager):
#   def setUp(self):
#     super().setUp()
#     ResourceManager._backend = ThreadedResourceQueue

#   # def test_resource_queue(self):
#   #   self.resource_queue_test(ThreadedResourceQueue, ThreadPoolExecutor)


# class TestMultiprocessResourceManger(TestResourceCase, CommonResourceManager):
#   def setUp(self):
#     super().setUp()
#     ResourceManager._backend = MultiprocessResourceQueue

#   def test_resource_queue(self):
#     self.resource_queue_test(MultiprocessResourceQueue, ProcessPoolExecutor)


# # class TestResourceManagerMulti(TestResourceCase, TestSettingsUnconfiguredCase):
# #   '''
# #   Test that ResourceManager backend picks the right Queue
# #   '''
# #   def setUp(self):
# #     super().setUp()
# #     settings.configure({'executor': {"type": "ProcessPoolExecutor"}})

# #   def test_thread_queue(self):
# #     ResourceManager.add_resource('test1', 2, 1)
# #     resource = ResourceManager.get_resource('test1')
# #     self.assertIsInstance(resource,
# #                           MultiprocessResourceQueue)

# #     # Prevent: https://stackoverflow.com/q/51680479/4166604
# #     while not resource.empty():
# #       resource.get()


# # class TestResourceManagerSingle(TestResourceCase, TestSettingsUnconfiguredCase):
# #   '''
# #   Test that ResourceManager backend picks the right Queue
# #   '''
# #   def setUp(self):
# #     super().setUp()
# #     settings.configure({'executor': {"type": "ThreadPoolExecutor"}})

# #   def test_thread_queue(self):
# #     ResourceManager.add_resource('test1', 2, 1)
# #     self.assertIsInstance(ResourceManager.get_resource('test1'),
# #                           ThreadedResourceQueue)


# class TestOtherThings(TestCase):
#   def last_test_stray_resources(self):
#     self.assertDictEqual(ResourceManager.queues, {})
