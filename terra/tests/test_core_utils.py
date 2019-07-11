from unittest import mock

from terra import settings
from .utils import TestCase
from terra.core.utils import cached_property

class CacheTest:
  def __init__(self):
    self.cached = 0

  @cached_property
  def foo(self):
    self.cached += 1
    return 13

class TestCachedProperty(TestCase):
  def test_cached_property(self):
    c = CacheTest()

    # Test that property hasn't been cached
    self.assertEqual(c.cached, 0)
    self.assertEqual(c.foo, 13)
    # Test that function was infact called
    self.assertEqual(c.cached, 1)

    self.assertEqual(c.foo, 13)
    self.assertEqual(c.foo, 13)
    # Verify it was only called onces
    self.assertEqual(c.cached, 1)

    # Test internal mechanics
    self.assertEqual(c.__dict__['foo'], 13)

  def test_class_mockability(self):
    # Test that mocking works
    with mock.patch.object(CacheTest, 'foo',
                           mock.PropertyMock(return_value=4)):
      c = CacheTest()
      self.assertEqual(c.foo, 4)
      self.assertEqual(c.cached, 0)

    # Test that property still hasn't been cached
    self.assertEqual(c.cached, 0)
    # Test that it was successfully restored
    self.assertEqual(c.foo, 13)
    # Test that function was infact called
    self.assertEqual(c.cached, 1)

    self.assertEqual(c.foo, 13)
    self.assertEqual(c.foo, 13)
    # Verify it was only called onces
    self.assertEqual(c.cached, 1)


  def test_instance_mockability(self):
    c = CacheTest()

    # Mock before cached
    with mock.patch.dict(c.__dict__, {'foo': 5}):
      self.assertEqual(c.foo, 5)
      self.assertEqual(c.cached, 0)

    # Test that property still hasn't been cached
    self.assertEqual(c.cached, 0)
    # Test that it was successfully restored
    self.assertEqual(c.foo, 13)
    # Test that function was infact called
    self.assertEqual(c.cached, 1)

    # Mock after cached
    with mock.patch.dict(c.__dict__, {'foo': 6}):
      self.assertEqual(c.foo, 6)
      self.assertEqual(c.cached, 1)

    self.assertEqual(c.foo, 13)
    self.assertEqual(c.foo, 13)
    # Verify it was only called onces
    self.assertEqual(c.cached, 1)

    # This should never be done, but the only way to re-execute a
    # cached_property
    c.__dict__.pop('foo')
    self.assertEqual(c.foo, 13)
    self.assertEqual(c.cached, 2)
