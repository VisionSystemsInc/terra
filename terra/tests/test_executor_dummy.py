from terra.executor.dummy import DummyExecutor
from .utils import TestCase


def test1(x):
  return 11 + x


def test2(x):
  if x == 11:
    raise AttributeError("foobar")
  return x + 13


class TestExecutorDummy(TestCase):
  def setUp(self):
    super().setUp()
    self.executor = DummyExecutor()

  def test_simple(self):
    future = self.executor.submit(test1, 15)
    self.assertEqual(future.result(), 26)

  def test_shutdown(self):
    self.assertEqual(self.executor.submit(test1, 15).result(), 26)
    self.executor.shutdown()
    with self.assertRaisesRegex(RuntimeError, "cannot .* after shutdown"):
      self.executor.submit(test1, 29)

  def test_exception(self):
    self.assertEqual(self.executor.submit(test2, 7).result(), 20)
    future = self.executor.submit(test2, 11)
    with self.assertRaisesRegex(AttributeError, "foobar"):
      raise future.exception()

  def test_map(self):
    mapped = self.executor.map(test1, [10, 11, 12])
    self.assertEqual(list(mapped), [21, 22, 23])
