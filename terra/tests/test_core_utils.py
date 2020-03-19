from unittest import mock

from .utils import TestCase
from terra.core.utils import (
    cached_property, Handler, ClassHandler
)


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

  def test_cached_property_set_name_not_called(self):
    def foo(self):
      return 15

    class Bar:
      pass

    Bar.test = cached_property(foo)

    with self.assertRaisesRegex(
        TypeError, 'Cannot use cached_property instance without calling'):
      Bar().test

  def test_cached_property_reuse_different_names(self):
    """
    Disallow this case because the decorated function wouldn't be cached.
    """
    with self.assertRaises(RuntimeError) as cm:
      class ReusedCachedProperty:
        @cached_property
        def a(self):
          pass
        b = a
    self.assertIn(
        "Cannot assign the same cached_property to two different names",
        str(cm.exception.__context__))

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
    with mock.patch.object(CacheTest, 'foo',
                           mock.PropertyMock(return_value=5)):
      self.assertEqual(c.foo, 5)
      self.assertEqual(c.cached, 0)

    # Test that property still hasn't been cached
    self.assertEqual(c.cached, 0)
    # Test that it was successfully restored
    self.assertEqual(c.foo, 13)
    # Test that function was infact called
    self.assertEqual(c.cached, 1)

    # Mock after cached
    with mock.patch.object(CacheTest, 'foo',
                           mock.PropertyMock(return_value=6)):
      self.assertEqual(c.foo, 6)
      self.assertEqual(c.cached, 1)

    self.assertEqual(c.foo, 13)
    self.assertEqual(c.foo, 13)
    # Verify it was only called onces
    self.assertEqual(c.cached, 1)

    # This should NEVER be done, but the only way to re-execute a
    # cached_property, which I'm testing here
    c.__dict__.pop('foo')
    self.assertEqual(c.foo, 13)
    self.assertEqual(c.cached, 2)


class TestHandler(TestCase):
  def test_handler_simple(self):
    handle = Handler()
    self.assertIs(handle._connection, int(0))

  def test_handler_override(self):
    class Foo:
      pass
    handle = Handler(override_type=Foo)
    self.assertIsInstance(handle._connection, Foo)

  def test_handler_attr(self):
    class Foo:
      pass

    handle = Handler(override_type=Foo)

    # Set on handle
    handle.bar = 15
    # Debug verify on connection
    self.assertEqual(handle._connection.bar, 15)

    # Emulate something in connection changing itself
    handle._connection.foo = 11
    # Verify on handler
    self.assertEqual(handle.foo, 11)

  def test_handler_del_attr(self):
    class Foo:
      pass

    handle = Handler(override_type=Foo)

    handle._connection.foo = 11
    handle.bar = 15

    del(handle.foo)
    self.assertFalse(hasattr(handle._connection, 'foo'))
    del(handle._connection.bar)
    self.assertFalse(hasattr(handle, 'bar'))

  def test_handler_autoconnect(self):
    handle = Handler()
    # Not connected
    self.assertNotIn('_connection', handle.__dict__)
    # Since the default is an int, int has a real property
    handle.real
    # Connected
    self.assertIn('_connection', handle.__dict__)
    self.assertIsNotNone(handle._connection)

  def test_close_handle(self):
    class Foo:
      def close(self):
        self.closed = True

    handle = Handler(override_type=Foo)
    handle.close()
    self.assertTrue(handle._connection.closed)

    handle = Handler(override_type=object)
    # Should not error
    handle.close()
    with self.assertRaises(AttributeError):
      handle.other()


class TestClassHandler(TestCase):
  def test_class_handler(self):
    class Bar:
      def __init__(self, x=17):
        self.x = x
    Ch = ClassHandler(override_type=Bar)
    self.assertIsInstance(Ch(), Bar)

    Ch = ClassHandler()
    self.assertIsInstance(Ch(), int)

  def test_class_handler_with_arguments(self):
    class Bar:
      def __init__(self, x=17):
        self.x = x
    Ch = ClassHandler(override_type=Bar)
    self.assertIsInstance(Ch(x=12), Bar)


class TestThreadedHandler(TestCase):
  def test_class_handler(self):
    pass
