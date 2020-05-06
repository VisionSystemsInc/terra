'''
A "signal dispatcher" class which helps allow decoupled componets get notified
when actions occur elsewhere in the framework. In a nutshell, signals allow
certain senders to notify a set of receivers that some action has taken place.
They're especially useful when many pieces of code may be interested in the
same events.

See https://docs.djangoproject.com/en/2.2/topics/signals/ for more info
'''

# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be
#        used to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import threading
import weakref

# Avoid importing anything else in terra here, it can cause some nasty
# interdependencies with logger. Import after post_settings_configured at the
# end of the file if you must...


def _make_id(target):
  if hasattr(target, '__func__'):
    return (id(target.__self__), id(target.__func__))
  return id(target)


NONE_ID = _make_id(None)
# A marker for caching
NO_RECEIVERS = object()


class Signal:
  """
  Base class for all signals

  Arguments
  ---------
  providing_args : list
      A list of the arguments this signal can pass along in a :func:`send`
      call.
  use_caching : bool
      If use_caching is ``True``, then for each distinct sender we cache the
      receivers that sender has in :data:`sender_receivers_cache`. The cache is
      cleaned when :func:`connect` or :func:`disconnect` is called and
      populated on :func:`send`.
  """

  def __init__(self, providing_args=None, use_caching=False):
    self.receivers = []
    '''dict: The internal map of all signals that are connected to receivers'''
    if providing_args is None:
      providing_args = []
    self.providing_args = set(providing_args)
    self.lock = threading.Lock()
    self.use_caching = use_caching
    '''bool: Set if caching was turned on'''
    # For convenience we create empty caches even if they are not used.
    # A note about caching: if use_caching is defined, then for each
    # distinct sender we cache the receivers that sender has in
    # 'sender_receivers_cache'. The cache is cleaned when .connect() or
    # .disconnect() is called and populated on send().
    self.sender_receivers_cache = weakref.WeakKeyDictionary() if use_caching \
        else {}
    '''weakref.WeakKeyDictionary: Stores receivers for a sender if
    :data:`use_caching` is on'''
    self._dead_receivers = False

  def connect(self, receiver, sender=None, weak=True, dispatch_uid=None):
    """
    Connect receiver to sender for signal.

    Parameters
    ----------
    receiver : :term:`function`
        A function or an instance method which is to receive signals.
        Receivers must be hashable objects.
        If weak is True, then receiver must be weak referenceable.
        Receivers must be able to accept keyword arguments.
        If a receiver is connected with a dispatch_uid argument, it
        will not be added if another receiver was already connected
        with that dispatch_uid.
    sender : object
        The sender to which the receiver should respond. Must either be
        a Python object, or None to receive events from any sender.
    weak : bool
        Whether to use weak references to the receiver. By default, the
        module will attempt to use weak references to the receiver
        objects. If this parameter is false, then strong references will
        be used.
    dispatch_uid : str
        An identifier used to uniquely identify a particular instance of
        a receiver. This will usually be a string, though it may be
        anything hashable.
    """

    if dispatch_uid:
      lookup_key = (dispatch_uid, _make_id(sender))
    else:
      lookup_key = (_make_id(receiver), _make_id(sender))

    if weak:
      ref = weakref.ref
      receiver_object = receiver
      # Check for bound methods
      if hasattr(receiver, '__self__') and hasattr(receiver, '__func__'):
        ref = weakref.WeakMethod
        receiver_object = receiver.__self__
      receiver = ref(receiver)
      weakref.finalize(receiver_object, self._remove_receiver)

    with self.lock:
      self._clear_dead_receivers()
      if not any(r_key == lookup_key for r_key, _ in self.receivers):
        self.receivers.append((lookup_key, receiver))
      self.sender_receivers_cache.clear()

  def disconnect(self, receiver=None, sender=None, dispatch_uid=None):
    """
    Disconnect receiver from sender for signal.

    If weak references are used, disconnect need not be called. The receiver
    will be removed from dispatch automatically.

    Parameters
    ----------
    receiver : :term:`function`
        The registered receiver to disconnect. May be none if
        dispatch_uid is specified.
    sender : object
        The registered sender to disconnect
    dispatch_uid : str
        the unique identifier of the receiver to disconnect
    """
    if dispatch_uid:
      lookup_key = (dispatch_uid, _make_id(sender))
    else:
      lookup_key = (_make_id(receiver), _make_id(sender))

    disconnected = False
    with self.lock:
      self._clear_dead_receivers()
      for index in range(len(self.receivers)):
        (r_key, _) = self.receivers[index]
        if r_key == lookup_key:
          disconnected = True
          del self.receivers[index]
          break
      self.sender_receivers_cache.clear()
    return disconnected

  def has_listeners(self, sender=None):
    return bool(self._live_receivers(sender))

  def send(self, sender, **named):
    """
    Send signal from sender to all connected receivers.

    If any receiver raises an error, the error propagates back through send,
    terminating the dispatch loop. So it's possible that all receivers
    won't be called if an error is raised.

    Parameters
    ----------
    sender : object
        The sender of the signal. Either a specific object or None.
    **named :
        Named arguments which will be passed to receivers.

    Returns
    -------
    list
        Return a list of tuple pairs [(receiver, response), ... ].
    """
    if not self.receivers or \
       self.sender_receivers_cache.get(sender) is NO_RECEIVERS:
      return []

    return [
        (receiver, receiver(signal=self, sender=sender, **named))
        for receiver in self._live_receivers(sender)
    ]

  def send_robust(self, sender, **named):
    """
    Send signal from sender to all connected receivers catching errors.

    Parameters
    ----------
    sender : object
        The sender of the signal. Can be any Python object (normally one
        registered with a connect if you actually want something to
        occur).
    **named :
        Named arguments which will be passed to receivers. These
        arguments must be a subset of the argument names defined in
        providing_args.

    Returns
    -------
    list
        Return a list of tuple pairs [(receiver, response), ... ].
        If any receiver raises an error (specifically any subclass of
        Exception), return the error instance as the result for that receiver.
    """
    if not self.receivers or \
       self.sender_receivers_cache.get(sender) is NO_RECEIVERS:
      return []

    # Call each receiver with whatever arguments it can accept.
    # Return a list of tuple pairs [(receiver, response), ... ].
    responses = []
    for receiver in self._live_receivers(sender):
      try:
        response = receiver(signal=self, sender=sender, **named)
      except Exception as err:
        responses.append((receiver, err))
      else:
        responses.append((receiver, response))
    return responses

  def _clear_dead_receivers(self):
    # Note: caller is assumed to hold self.lock.
    if self._dead_receivers:
      self._dead_receivers = False
      self.receivers = [
          r for r in self.receivers
          if not (isinstance(r[1], weakref.ReferenceType) and r[1]() is None)
      ]

  def _live_receivers(self, sender):
    """
    Filter sequence of receivers to get resolved, live receivers.

    This checks for weak references and resolves them, then returning only
    live receivers.
    """
    receivers = None
    if self.use_caching and not self._dead_receivers:
      receivers = self.sender_receivers_cache.get(sender)
      # We could end up here with NO_RECEIVERS even if we do check this case in
      # .send() prior to calling _live_receivers() due to concurrent .send()
      # call.
      if receivers is NO_RECEIVERS:
        return []
    if receivers is None:
      with self.lock:
        self._clear_dead_receivers()
        senderkey = _make_id(sender)
        receivers = []
        for (receiverkey, r_senderkey), receiver in self.receivers:
          if r_senderkey == NONE_ID or r_senderkey == senderkey:
            receivers.append(receiver)
        if self.use_caching:
          if not receivers:
            self.sender_receivers_cache[sender] = \
                NO_RECEIVERS
          else:
            # Note, we must cache the weakref versions.
            self.sender_receivers_cache[sender] = receivers
    non_weak_receivers = []
    for receiver in receivers:
      if isinstance(receiver, weakref.ReferenceType):
        # Dereference the weak reference.
        receiver = receiver()
        if receiver is not None:
          non_weak_receivers.append(receiver)
      else:
        non_weak_receivers.append(receiver)
    return non_weak_receivers

  def _remove_receiver(self, receiver=None):
    # Mark that the self.receivers list has dead weakrefs. If so, we will
    # clean those up in connect, disconnect and _live_receivers while
    # holding self.lock. Note that doing the cleanup here isn't a good
    # idea, _remove_receiver() will be called as side effect of garbage
    # collection, and so the call can happen while we are already holding
    # self.lock.
    self._dead_receivers = True


def receiver(signal, **kwargs):
  """
  A decorator for connecting receivers to signals.

  Used by passing in the signal (or list of signals) and keyword arguments to
  connect:

  Arguments
  ---------
  signal : Signal
      The signal registering against
  **kwargs :
      Additional arguments to send to the :func:`Signal.connect` function

  Examples
  --------

  >>> @receiver(post_save, sender=MyModel)
  ... def signal_receiver(sender, **kwargs):
  ...     stuff()

  >>> @receiver([post_save, post_delete], sender=MyModel)
  ... def signals_receiver(sender, **kwargs):
  ...     stuff()
  """

  def _decorator(func):
    if isinstance(signal, (list, tuple)):
      for s in signal:
        s.connect(func, **kwargs)
    else:
      signal.connect(func, **kwargs)
    return func

  return _decorator


__all__ = ['Signal', 'receiver', 'post_settings_configured',
           'post_settings_context', 'logger_configure', 'logger_reconfigure']

# a signal for settings done being loaded
post_settings_configured = Signal()
'''Signal:
Sent after settings has been configured. This will either happen after
:func:`terra.core.settings.LazySettings._setup` is trigger by accessing any
element in the settings (which is done automatically), or in rare cases after a
manual call to :func:`terra.core.settings.LazySettings.configure`.
'''

post_settings_context = Signal()
'''Signal:
Sent after scope __exit__ from a settings context (i.e., with statement).
'''

# REVIEW should this be called post_logger_configure
logger_configure = Signal()
'''Signal:
Sent to the executor after the logger has been configured. This will happen
after the post_settings_configured signal.
'''

logger_reconfigure = Signal()
'''Signal:
Sent to the executor after the logger has been reconfigured. This will happen
after the logger_configure signal.
'''

from terra.logger import getLogger  # noqa
logger = getLogger(__name__)
# Must be after post_settings_configured to prevent circular import errors.
# Just can't use logger during import (global scope)
# This also works. Just "import terra.logger" does not, because logger isn't
# done being imported here
# import terra.logger as terra_logger
# terra_logger = terra_logger.getLogger(__name__)
