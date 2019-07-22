import sys
import os
import time
from unittest import mock, skipUnless

try:
  import celery
except:   # noqa
  celery = None

from .utils import TestCase


@skipUnless(celery, "Celery not installed")
class TestCeleryConfig(TestCase):
  def setUp(self):
    self.patches.append(mock.patch.dict(os.environ,
                                        TERRA_CWD=self.temp_dir.name))
    self.patches.append(mock.patch.dict(os.environ,
                                        TERRA_REDIS_SECRET_FILE='foo'))
    with open(os.path.join(self.temp_dir.name, 'foo'), 'w') as fid:
      fid.write('hiya')
    super().setUp()

  def tearDown(self):
    super().tearDown()

    if 'terra.executor.celery.celeryconfig' in sys.modules:
      sys.modules.pop('terra.executor.celery.celeryconfig')

  def test_no_redis_passwordfile(self):
    os.remove(os.path.join(self.temp_dir.name, 'foo'))
    with self.assertRaises(FileNotFoundError), self.assertLogs():
      import terra.executor.celery.celeryconfig  # noqa

  def test_redis_passwordfile(self):
    import terra.executor.celery.celeryconfig as cc
    self.assertEqual(cc.password, 'hiya')

  @mock.patch.dict(os.environ, TERRA_CELERY_INCLUDE='["foo", "bar"]')
  def test_include(self):
    import terra.executor.celery.celeryconfig as cc
    self.assertEqual(cc.include, ['foo', 'bar'])


class MockAsyncResult:
  def __init__(self, id, fun):
    self.id = id
    self.fun = fun
    self.forgotten = False

  def ready(self):
    return True
  state = 'SUCCESS'

  def revoke(self):
    self.state = 'REVOKED'

  def get(self, *args, **kwargs):
    return self.fun(self)

  def forget(self):
    self.forgotten = True


def test_factory():
  def test(self):
    return 17
  test.apply_async = lambda args, kwargs: MockAsyncResult(1, test)

  return test


@skipUnless(celery, "Celery not installed")
class TestCeleryExecutor(TestCase):
  def setUp(self):
    super().setUp()
    from terra.executor.celery import CeleryExecutor
    self.executor = CeleryExecutor(update_delay=0.001)

  def tearDown(self):
    super().tearDown()
    self.executor._monitor_stopping = True
    try:
      self.executor._monitor.join()
    except RuntimeError:
      # Thread never started. Cannot join
      pass

  def wait_for_state(self, future, state):
    for x in range(100):
      time.sleep(0.001)
      if future._state == state:
        break
      if x == 99:
        raise TimeoutError(f'Took longer than 100us for a 1us update for '
                           f'{future._state} to become {state}')

  def test_simple(self):
    test = test_factory()
    future = self.executor.submit(test)
    future.result()

  def test_cancel(self):
    test = test_factory()
    future = self.executor.submit(test)
    future._ar.state = 'RECEIVED'

    # Cancels!
    self.assertTrue(future.cancel())

    self.assertEqual(future._state, 'CANCELLED')
    self.assertEqual(future._ar.state, 'REVOKED')

  def test_cancel_uncancellable(self):
    test = test_factory()
    future = self.executor.submit(test)
    future._ar.state = 'RECEIVED'

    # Make revoking fail
    future._ar.revoke = lambda: True

    # Fails to cancel
    self.assertFalse(future.cancel())

    self.assertEqual(future._state, 'PENDING')
    self.assertEqual(future._ar.state, 'RECEIVED')

  def test_cancel_running(self):
    test = test_factory()
    future = self.executor.submit(test)
    future._ar.state = 'RUNNING'
    future._state = 'RUNNING'

    # Fails to cancel
    self.assertFalse(future.cancel())

    self.assertEqual(future._state, 'RUNNING')
    self.assertEqual(future._ar.state, 'RUNNING')

  def test_update_futures_running(self):
    test = test_factory()
    future = self.executor.submit(test)

    self.assertFalse(future.running())
    future._ar.state = 'RUNNING'
    self.wait_for_state(future, 'RUNNING')
    self.assertTrue(future.running())

  def test_update_futures_finish(self):
    test = test_factory()
    future = self.executor.submit(test)
    future._state = 'FINISHED'

    self.assertEqual(len(self.executor._futures), 1)

    for x in range(100):
      time.sleep(0.001)
      if not len(self.executor._futures):
        break
      if x == 99:
        raise TimeoutError('Took longer than 100us for a 1us update')

  def test_update_futures_revoked(self):
    test = test_factory()
    future = self.executor.submit(test)

    self.assertFalse(future.cancelled())
    future._ar.state = 'REVOKED'
    self.wait_for_state(future, 'CANCELLED_AND_NOTIFIED')
    self.assertTrue(future.cancelled())

  def test_update_futures_success(self):
    test = test_factory()
    future = self.executor.submit(test)

    self.assertIsNone(future._result)
    future._ar.state = 'SUCCESS'
    self.wait_for_state(future, 'FINISHED')
    self.assertEqual(future._result, 17)

  def test_update_futures_failure(self):
    test = test_factory()
    future = self.executor.submit(test)

    self.assertIsNone(future._result)
    future._ar.state = 'FAILURE'
    future._ar.result = TypeError('On no')
    self.wait_for_state(future, 'FINISHED')

  def test_shutdown(self):
    test = test_factory()
    self.assertEqual(self.executor.submit(test).result(), 17)
    self.executor.shutdown()
    with self.assertRaisesRegex(RuntimeError, "cannot .* after shutdown"):
      self.executor.submit(test)

  def test_import(self):
    import terra.executor.celery
    from celery._state import _apps
    # import pdb; pdb.set_trace()
    print([a for a in _apps])