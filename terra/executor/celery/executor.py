# Based off of https://github.com/getninjas/celery-executor/
#
# Apache Software License 2.0
#
# Copyright (c) 2018, Alan Justino da Silva
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import atexit
from os import environ as env
from terra.executor.base import BaseFuture, BaseExecutor
from concurrent.futures import as_completed
from concurrent.futures._base import (RUNNING, FINISHED, CANCELLED,
                                      CANCELLED_AND_NOTIFIED)
from threading import Lock, Thread
import time
import logging.handlers
import pickle
import socketserver
import struct
import threading

from celery.signals import setup_logging

import terra
from terra import settings
from terra.logger import getLogger
logger = getLogger(__name__)


# stop celery from hijacking the logger
@setup_logging.connect
def setup_loggers(*args, **kwargs):
  print("SGR - celery logger")

class CeleryExecutorFuture(BaseFuture):
  def __init__(self, asyncresult):
    self._ar = asyncresult
    super().__init__()

  def __del__(self):
    self._ar.forget()
    del self._ar

  def cancel(self):
    """Cancel the future if possible.
    Returns True if the future was cancelled, False otherwise. A future
    cannot be cancelled if it is running or has already completed.
    """
    logger.info(f'Canceling task {self._ar.id}')
    with self._condition:
      if self._state in [RUNNING, FINISHED, CANCELLED, CANCELLED_AND_NOTIFIED]:
        return super().cancel()

      # Not running and not canceled. May be possible to cancel!
      self._ar.ready()  # Triggers an update check
      if self._ar.state != 'REVOKED':
        self._ar.revoke()
        self._ar.ready()

      # Celery task should be REVOKED now. Otherwise may be not possible
      # revoke it.
      if self._ar.state == 'REVOKED':
        result = super().cancel()
        if not result:  # pragma: no cover
          logger.error('Please open an issue on Github: Upstream '
                       'implementation changed?')
      else:
        # Is not running nor revoked nor finished :/
        # The revoke() had not produced effect: Task is probable not on a
        # worker, then not revoke-able.
        # Setting as RUNNING to inhibit super() from cancelling the Future,
        # then putting back.
        initial_state = self._state
        self._state = RUNNING
        result = super().cancel()
        if result:  # pragma: no cover
          logger.error('Please open an issue on Github: Upstream '
                       'implementation changed?')
        self._state = initial_state

      return result


class CeleryExecutor(BaseExecutor):
  """
  Executor implementation using celery tasks.

  Parameters
  ----------
  predelay
      Will trigger before the `.apply_async` internal call
  postdelay
      Will trigger before the `.apply_async` internal call
  applyasync_kwargs
      Options passed to the `.apply_async()` call
  retry_kwargs
      Options passed to the `.retry()` call on errors
  retry_queue
      Sugar to set an alternative queue specially for errors
  update_delay
      Delay time between checks for Future state changes
  """

  def __init__(self, predelay=None, postdelay=None, applyasync_kwargs=None,
               retry_kwargs=None, retry_queue='', update_delay=0.1,
               max_workers=None):
    # Options about calling the Task
    self._predelay = predelay
    self._postdelay = postdelay
    self._applyasync_kwargs = applyasync_kwargs or {}
    self._retry_kwargs = retry_kwargs or {}
    if retry_queue:
      self._retry_kwargs['queue'] = retry_queue
      self._retry_kwargs.setdefault('max_retries', 1)
    self._retry_kwargs.setdefault('max_retries', 0)

    # Options about managing this Executor flow
    self._update_delay = update_delay
    self._shutdown = False
    self._shutdown_lock = Lock()
    self._futures = set()
    self._monitor_started = False
    self._monitor_stopping = False
    self._monitor = Thread(target=self._update_futures)
    self._monitor.setDaemon(True)

  def _update_futures(self):
    while True:
      time.sleep(self._update_delay)  # Not-so-busy loop
      if self._monitor_stopping:
        return

      for fut in tuple(self._futures):
        if fut._state in (FINISHED, CANCELLED_AND_NOTIFIED):
          # This Future is set and done. Nothing else to do.
          self._futures.remove(fut)
          continue

        ar = fut._ar
        ar.ready()  # Just trigger the AsyncResult state update check

        if ar.state == 'REVOKED':
          logger.warning('Celery task "%s" canceled.', ar.id)
          if not fut.cancelled():
            if not fut.cancel():  # pragma: no cover
              logger.error('Future was not running but failed to be cancelled')
            fut.set_running_or_notify_cancel()
          # Future is CANCELLED -> CANCELLED_AND_NOTIFIED

        elif ar.state in ('RUNNING', 'RETRY'):
          logger.debug4('Celery task "%s" running.', ar.id)
          if not fut.running():
            fut.set_running_or_notify_cancel()
          # Future is RUNNING

        elif ar.state == 'SUCCESS':
          logger.debug4('Celery task "%s" resolved.', ar.id)
          fut.set_result(ar.get(disable_sync_subtasks=False))
          # Future is FINISHED

        elif ar.state == 'FAILURE':
          logger.info('Celery task "%s" resolved with error.', ar.id)
          fut.set_exception(ar.result)
          # Future is FINISHED

        # else:  # ar.state in [RECEIVED, STARTED, REJECTED, RETRY]
        #     pass

  def submit(self, fn, *args, **kwargs):
    """
    """  # Original python comment has * and isn't napoleon compatible
    with self._shutdown_lock:
      if self._shutdown:
        raise RuntimeError('cannot schedule new futures after shutdown')

      if not self._monitor_started:
        self._monitor.start()
        self._monitor_started = True

      # metadata = {
      #     'retry_kwargs': self._retry_kwargs.copy()
      # }

      if self._predelay:
        self._predelay(fn, *args, **kwargs)
      # asyncresult = _celery_call.apply_async((fn, metadata) + args, kwargs,
      #                                        **self._applyasync_kwargs)
      asyncresult = fn.apply_async(args, kwargs)

      if self._postdelay:
        self._postdelay(asyncresult)

      future = CeleryExecutorFuture(asyncresult)
      self._futures.add(future)
      return future

  def shutdown(self, wait=True):
    logger.info('Shutting down celery tasks...')
    with self._shutdown_lock:
      self._shutdown = True
      for fut in tuple(self._futures):
        fut.cancel()

    if wait:
      for _ in as_completed(self._futures):
        pass

      self._monitor_stopping = True
      try:
        self._monitor.join()
      except RuntimeError:  # pragma: no cover
        # Thread never started. Cannot join
        pass

  @staticmethod
  def configuration_map(service_info):
    from terra.compute import compute
    service_name = env['TERRA_CELERY_SERVICE']

    class ServiceClone:
      def __init__(self, service_info):
        self.compose_service_name = service_name

        if hasattr(service_info, 'justfile'):
          self.justfile = service_info.justfile
        if hasattr(service_info, 'compose_files'):
          self.compose_files = service_info.compose_files

        self.env = env  # .copy()
        self.volumes = []

    service_clone = ServiceClone(service_info)

    if hasattr(compute, 'config'):
      config = compute.config(service_clone)
    else:
      config = None

    volume_map = compute.get_volume_map(config, service_clone)

    return volume_map

  @staticmethod
  def configure_logger(sender, **kwargs):
    sender._hostname = settings.logging.server.hostname
    sender._port = settings.logging.server.port

    if settings.terra.zone == 'controller':
      print("SGR - setting up controller logging")

      super(CeleryExecutor, CeleryExecutor).configure_logger(sender, **kwargs)

      # setup the listener
      sender.tcp_logging_server = LogRecordSocketReceiver(sender._hostname, sender._port)
      print('SGR - About to start TCP server...')

      lp = threading.Thread(target=sender.tcp_logging_server.serve_until_stopped)
      lp.setDaemon(True)
      # FIXME can't actually handle a log message until logging is done configuring
      lp.start()

      @atexit.register
      def cleanup_thread():
        print("SGR - Sending cease and desist to LogRecordSocketReceiver")
        sender.tcp_logging_server.abort = 1
        lp.join(timeout=5)
        if lp.is_alive():
          print("SGR - LogRecordSocketReceiver thread did not die")
        print("SGR - LogRecordSocketReceiver died!")

    elif settings.terra.zone == 'runner' or settings.terra.zone == 'task':
      print(f"SGR - setting up {settings.terra.zone} logging")

      sender._socket_handler = logging.handlers.SocketHandler(sender._hostname,
          sender._port)

      # TODO don't bother with a formatter, since a socket handler sends the event
      # as an unformatted pickle

      sender.main_log_handler = sender._socket_handler
    elif settings.terra.zone == 'task_controller':
      print("SGR - setting up task_controller logging")

      super(CeleryExecutor, CeleryExecutor).configure_logger(sender, **kwargs)
    else:
      assert False, 'unknown zone: ' + settings.terra.zone

  @staticmethod
  def reconfigure_logger(sender, **kwargs):
    # FIXME no idea how to reset this
    # setup the logging when a task is reconfigured; e.g., changing logging
    # level or hostname

    if settings.terra.zone == 'runner' or settings.terra.zone == 'task':
      print("SGR - reconfigure runner/task logging")

      # when the celery task is done, its logger is automatically reconfigured;
      # use that opportunity to close the stream
      if hasattr(sender, '_socket_handler'):
        sender._socket_handler.close()

# from https://docs.python.org/3/howto/logging-cookbook.html
class LogRecordStreamHandler(socketserver.StreamRequestHandler):
  """Handler for a streaming logging request.

  This basically logs the record using whatever logging policy is
  configured locally.
  """

  def handle(self):
    """
    Handle multiple requests - each expected to be a 4-byte length,
    followed by the LogRecord in pickle format. Logs the record
    according to whatever policy is configured locally.
    """
    while True:
      chunk = self.connection.recv(4)
      if len(chunk) < 4:
        break
      slen = struct.unpack('>L', chunk)[0]
      chunk = self.connection.recv(slen)
      while len(chunk) < slen:
        chunk = chunk + self.connection.recv(slen - len(chunk))
      obj = self.unPickle(chunk)
      record = logging.makeLogRecord(obj)
      self.handleLogRecord(record)

  def unPickle(self, data):
    return pickle.loads(data)

  def handleLogRecord(self, record):
    # if a name is specified, we use the named logger rather than the one
    # implied by the record.
    if self.server.logname is not None:
      name = self.server.logname
    else:
      name = record.name
    logger = terra.logger.getLogger(name)
    # N.B. EVERY record gets logged. This is because Logger.handle
    # is normally called AFTER logger-level filtering. If you want
    # to do filtering, do it at the client end to save wasting
    # cycles and network bandwidth!
    logger.handle(record)

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
  """
  Simple TCP socket-based logging receiver suitable for testing.
  """

  allow_reuse_address = True

  def __init__(self, host='localhost',
               port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
               handler=LogRecordStreamHandler):
    socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
    self.abort = 0
    self.timeout = 1
    self.logname = None

  def serve_until_stopped(self):
    import select
    abort = 0
    print('SGR - STARTING LISTNER')
    while not abort:
      rd, wr, ex = select.select([self.socket.fileno()],
                                  [], [],
                                  self.timeout)
      if rd:
        print('SGR - RD')
        self.handle_request()
      abort = self.abort
