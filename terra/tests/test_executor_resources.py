import os
from concurrent.futures import (
  ThreadPoolExecutor, ProcessPoolExecutor, as_completed
)

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
