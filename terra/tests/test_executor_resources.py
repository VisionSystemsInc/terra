import os
from concurrent.futures import (
  ThreadPoolExecutor, ProcessPoolExecutor, as_completed
)
from unittest import mock
import terra.filelock
import platform

from terra.tests.utils import TestSettingsConfiguredCase, TestSettingsUnconfiguredCase, TestCase
from terra.executor.resources import (
  Resource, ResourceError
)
from terra import settings

class TestResource(TestSettingsConfiguredCase):
  def test_dir(self):
    resource = Resource('test', 1, 1)
    self.assertFalse(os.path.exists(resource.lock_dir))
    resource.acquire()
    self.assertTrue(os.path.exists(resource.lock_dir))
    resource.release()
    # self.assertFalse(os.path.exists(resource.lock_dir))
    # os.makedirs(resource.lock_dir)

    with self.assertLogs('terra.executor.resources', level='WARNING') as cm:
      resource = Resource('test', 1, 1, True)

    self.assertIn('is not empty. Deleting it now...', cm.output[0])
    self.assertFalse(os.path.exists(resource.lock_dir))

  def test_enter(self):
    resource = Resource('test', 2, 1)
    r1 = resource.__enter__()
    r2 = resource.__enter__()

    self.assertEqual(r1, r2)

data = {}

class TestResourceSingle(TestSettingsUnconfiguredCase):
  def setUp(self):
    super().setUp()
    settings.configure({'executor': {"type": 'SyncExecutor'},
                        'processing_dir': self.temp_dir.name})

  def test_acquire_single(self):
    lock_dir = os.path.join(settings.processing_dir, '.resource.locks',
                            platform.node(), str(os.getpid()), 'single')
    self.assertNotExist(lock_dir)
    test1 = Resource('single', 2, 1)
    self.assertNotExist(lock_dir)

    lock1 = test1.acquire()
    lock2 = test1.acquire()

    # Acquiring twice, should use the cached value
    self.assertEqual(lock1, lock2)

    test2 = Resource('single', 2, 1)
    lock3 = test2.acquire()
    # However, using an entirely different resource instance, won't have cache
    self.assertNotEqual(lock1, lock3)

    # At this point, I should be out of resources
    test3 = Resource('single', 2, 1)
    with self.assertRaises(ResourceError):
      test3.acquire()

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

    # Four unique names
    self.assertEqual(len({repeat1._local.lock.lock_file,
                          repeat2._local.lock.lock_file,
                          repeat3._local.lock.lock_file,
                          repeat4._local.lock.lock_file}), 4)

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


# Cannot be member of test case class, because testcase's _outcome cannot be
# pickled "cannot serialize '_io.TextIOWrapper' object" error somewhere in
# there
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

  def test_acquire(self):
    data[self.name] = Resource(self.name, 2, 1)

    futures = []
    results = []
    exceptions = 0

    with self.Executor(max_workers=3) as executor:
      for _ in range(3):
        futures.append(executor.submit(acquire, self.name))

      for future in as_completed(futures):
        try:
          results.append(future.result())
        except ResourceError:
          exceptions += 1

    self.assertEqual(exceptions, 1)

    self.assertNotEqual(results[0], results[1])
    self.assertEqual(results[0][0], results[0][1])
    self.assertEqual(results[1][0], results[1][1])

class TestResourceThread(TestResource,
                         TestSettingsUnconfiguredCase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.Executor = ThreadPoolExecutor
    self.name = "ThreadPoolExecutor"

class TestResourceProcess(TestResource,
                          TestSettingsUnconfiguredCase):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.Executor = ProcessPoolExecutor
    self.name = "ProcessPoolExecutor"

# from .utils import TestCase, TestResourceCase, TestSettingsUnconfiguredCase
# from terra import settings
# from terra.executor.resources import (
#   ResourceQueueMixin, ResourceManager, ThreadedResourceQueue,
#   MultiprocessResourceQueue, Empty, Full
# )


# class TestResourceQueue(TestCase):
#   def test_get(self):
#     pass #ResourceManager.add_resource('test', 2, 1)

# global_data = {}

# def get_resource():
#   return global_data['test1'].get(True, 0.1)

# def put_resource(obj):
#   global_data['test1'].put(obj, True, 0.1)

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
