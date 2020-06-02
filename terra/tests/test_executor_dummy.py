from terra.executor import dummy
from .utils import TestSettingsConfiguredCase


def test1(x):
  return 11 + x


def test2(x):
  return x + 13


class TestExecutorDummy(TestSettingsConfiguredCase):
  def setUp(self):
    super().setUp()
    self.executor = dummy.DummyExecutor()

  def test_simple(self):
    future = self.executor.submit(test1, 15)
    self.assertEqual(future.result(), None)

  def test_shutdown(self):
    self.assertEqual(self.executor.submit(test1, 15).result(), None)
    self.executor.shutdown()
    with self.assertRaisesRegex(RuntimeError, "cannot .* after shutdown"):
      self.executor.submit(test1, 29)

  def test_map(self):
    mapped = self.executor.map(test1, [10, 11, 12])
    self.assertEqual(list(mapped), [None, None, None])

  def test_run(self):
    class DummyFunction:
      def __str__(self):
        return "FooFun"

    with self.assertLogs(dummy.__name__, level="INFO") as cm:
      self.executor.submit(DummyFunction(), 15, x=12)

    self.assertIn('Run function: FooFun', str(cm.output))
    self.assertIn('With args: (15,)', str(cm.output))
    self.assertIn("With kwargs: {'x': 12}", str(cm.output))
