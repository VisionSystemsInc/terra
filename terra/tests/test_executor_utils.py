from unittest import SkipTest
import concurrent.futures

from terra import settings
from .utils import TestCase, TestExecutorCase, TestSettingsUnconfiguredCase
from terra.executor.utils import ExecutorHandler, Executor
from terra.executor.dummy import DummyExecutor
from terra.executor.sync import SyncExecutor


class TestExecutorHandler(TestExecutorCase, TestSettingsUnconfiguredCase):
  def test_executor_handler(self):
    settings.configure({'executor': {'type': 'DummyExecutor'}})

    test_executor = ExecutorHandler()

    self.assertIsNotNone(test_executor._connection)
    self.assertIsInstance(test_executor._connection(), DummyExecutor)

  # Make sure this can be run twice
  test_executor_handler2 = test_executor_handler

  def test_executor(self):
    settings.configure({'executor': {'type': 'DummyExecutor'}})

    executee = Executor()

    self.assertIsNotNone(Executor._connection)
    self.assertIsInstance(Executor._connection(), DummyExecutor)
    self.assertIsInstance(executee, DummyExecutor)

  def test_executor_name_sync(self):
    settings.configure({'executor': {'type': 'SyncExecutor'}})
    self.assertIsInstance(Executor._connection(), SyncExecutor)

  # TODO: It takes more mocking to make this test pass now
  # def test_executor_name_thread(self):
  #   settings.configure({'executor': {'type': 'ThreadPoolExecutor'}})
  #   self.assertIsInstance(Executor._connection(),
  #                         concurrent.futures.ThreadPoolExecutor)

  def test_executor_name_process(self):
    settings.configure({'executor': {'type': 'ProcessPoolExecutor'}})
    self.assertIsInstance(Executor._connection(),
                          concurrent.futures.ProcessPoolExecutor)

  def test_executor_name_celery(self):
    try:
      import terra.executor.celery
    except ImportError:
      raise SkipTest('Celery does not appear to be installed')

    settings.configure({'executor': {'type': 'CeleryExecutor'}})
    self.assertIsInstance(Executor._connection(),
                          terra.executor.celery.CeleryExecutor)

  def test_executor_name_by_name(self):
    settings.configure(
        {'executor': {'type': 'concurrent.futures.ProcessPoolExecutor'}})
    self.assertIsInstance(Executor._connection(),
                          concurrent.futures.ProcessPoolExecutor)


class TestUnitTests(TestCase):
  # Don't name this "test*" so normal discover doesn't pick it up, "last*" are
  # run last
  def last_test_executor_handler(self):
    self.assertNotIn(
        '_connection', Executor.__dict__,
        msg="If you are seeing this, one of the other unit tests has "
            "initialized the Executor connection. This side effect should be "
            "prevented by mocking out the _connection attribute, or "
            "'mock.patch.dict(Executor.__dict__)'. Otherwise unit tests can "
            "interfere with each other. Add 'import traceback; "
            "traceback.print_stack()' to ExecutorHandler._connect_backend")
