from terra.core.signals import Signal, receiver
import terra.core.signals as signals
from .utils import TestCase, TestSignalCase

class TestSignals(TestSignalCase):
  def signal_handle1(self, sender, **kwargs):
    self.assertEqual(sender, self.sender)
    self.kwargs = kwargs
    return 57

  def test_signal(self):
    self.signal = Signal()

    self.signal.connect(self.signal_handle1)

    self.sender = object()
    self.assertEqual(self.signal.send(sender=self.sender),
                     [(self.signal_handle1, 57)])
    self.assertEqual(self.kwargs, {'signal': self.signal})

  def test_signal_providing_args(self):
    self.signal = Signal(['foo'])

    self.assertFalse(self.signal.has_listeners())
    self.signal.connect(self.signal_handle1)
    self.assertTrue(self.signal.has_listeners())

    self.sender = object()
    self.signal.send(sender=self.sender, foo='bar')
    self.assertEqual(self.kwargs, {'foo': 'bar', 'signal': self.signal})

  def cache1(self, *args, **kwargs):
    return 12

  def test_cache(self):
    class Stuff:
      pass

    self.signal = Signal(use_caching=True)
    self.signal.connect(self.cache1)
    self.sender = Stuff()
    self.assertEqual(self.signal.send(sender=self.sender), [(self.cache1, 12)])

  def fail1(self, *args, **kwargs):
    self.assertTrue(0)

  def test_signal_dispatch_id(self):
    self.signal = Signal()

    self.signal.connect(self.signal_handle1, dispatch_uid=37)
    self.signal.connect(self.fail1, dispatch_uid=37)
    self.sender = object()
    self.signal.send(sender=self.sender)

  def test_signal_sender(self):
    # Sender match
    self.sender = object()
    self.signal = Signal(['foo'])
    self.assertFalse(self.signal.has_listeners())
    self.signal.connect(self.signal_handle1, sender=self.sender)
    self.assertFalse(self.signal.has_listeners())
    self.assertTrue(self.signal.has_listeners(sender=self.sender))
    self.signal.send(sender=self.sender, foo=1)
    self.assertEqual(self.kwargs['foo'], 1)
    # Sender miss
    self.signal.connect(self.fail1, sender=object())
    self.signal.send(sender=self.sender)

    # Sender miss by self
    self.signal = Signal()
    self.signal.connect(self.fail1, sender=object())
    self.signal.send(sender=self.sender)

  def test_disconnect(self):
    self.sender = object()
    self.signal = Signal(['foo'])
    self.signal.connect(self.fail1)
    with self.assertRaises(AssertionError):
      self.signal.send(sender=self.sender)
    self.signal.disconnect(self.fail1)
    self.signal.send(sender=self.sender)

    # dispatch uid
    self.sender = object()
    self.signal = Signal(['foo'])
    self.signal.connect(self.fail1, dispatch_uid=37)
    with self.assertRaises(AssertionError):
      self.signal.send(sender=self.sender)

    self.signal.disconnect(self.fail1)
    with self.assertRaises(AssertionError):
      self.signal.send(sender=self.sender)

    self.signal.disconnect(self.fail1, dispatch_uid=35)
    with self.assertRaises(AssertionError):
      self.signal.send(sender=self.sender)

    self.signal.disconnect(self.fail1, dispatch_uid=37)
    self.signal.send(sender=self.sender)

    # sender
    self.sender = object()
    self.signal = Signal(['foo'])
    self.signal.connect(self.fail1, sender=self.sender)
    with self.assertRaises(AssertionError):
      self.signal.send(sender=self.sender)

    self.signal.disconnect(self.fail1)
    with self.assertRaises(AssertionError):
      self.signal.send(sender=self.sender)

    self.signal.disconnect(self.fail1, sender=self.sender)
    self.signal.send(sender=self.sender)

  def fail2(self):
    raise TypeError('Foo is not Bar')

  def test_robust(self):
    self.sender = object()
    self.signal = Signal()
    self.signal.connect(self.fail1)
    self.signal.connect(self.fail2)
    self.signal.connect(self.signal_handle1)
    with self.assertRaises(AssertionError):
      self.signal.send(sender=self.sender)

    results = self.signal.send_robust(self.sender)
    self.assertEqual(results[0][0], self.fail1)
    self.assertIsInstance(results[0][1], AssertionError)
    self.assertEqual(results[1][0], self.fail2)
    self.assertIsInstance(results[1][1], TypeError)
    self.assertEqual(results[2][0], self.signal_handle1)
    self.assertEqual(results[2][1], 57)

  def test_decorator(self):
    self.signal = Signal()
    self.sender = object()

    @receiver(self.signal)
    def decorated1(sender, **kwargs):
      self.count += 1

    @receiver([self.signal, self.signal])
    def decorated2(sender, **kwargs):
      self.count += 0.1

    self.count = 0.0
    self.signal.send(sender=self.sender)
    self.assertEqual(self.count, 1.1)


# This no longer matters, as signals are disabled in unitted tests now?
# class TestUnitTests(TestCase):
#   def last_test_signals(self):
#     for signal in [signals.post_settings_configured,
#                    signals.post_settings_context,
#                    signals.logger_configure,
#                    signals.logger_reconfigure]:
#       self.assertFalse(
#           signal.receivers,
#           msg="If you are seeing this, one of the other unit tests has "
#               "left a signal connected. This side effect should "
#               "be prevented by disconnecting any functions you connected to a "
#               "signal.")
