from unittest import TestCase as TestCaseOriginal
from tempfile import TemporaryDirectory


class TestCase(TestCaseOriginal):
  '''
  TestCase class for terra tests

  * Auto creates ``self.temp_dir``, a self deleting temporary directory for
    each test
  * Initialized ``self.patches`` to an empty list, so you can append patches
  * On ``setUp``, auto starts all ``self.patches``
  * On tearDown, auto stops all ``self.patches``

  .. rubric:: Example

  .. code-block:: python

      class TestSomething(terra.test.utils.TestCase):
        def setUp(self):
          self.patches.append(mock.patch.object(settings, '_wrapped', None))
          super().setUp()
          settings.configure({'foo': 15})
        def test_something(self):
          print(self.temp_dir.name)
          self.assertEqual(settings.foo, 15)
  '''

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.patches = []
    self._temp_dir = None

  @property
  def temp_dir(self):
    if self._temp_dir is None:
      self._temp_dir = TemporaryDirectory()
    return self._temp_dir

  def setUp(self):
    for patch in self.patches:
      patch.start()

  def tearDown(self):
    if self._temp_dir is not None:
      self._temp_dir.cleanup()
    while self.patches:
      self.patches.pop().stop()
