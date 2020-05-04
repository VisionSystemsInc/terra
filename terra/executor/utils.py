import os
import logging
import concurrent.futures
from importlib import import_module

from terra import settings
from terra.core.utils import ClassHandler
import terra.logger

import logging.handlers
import pickle
import socketserver
import struct
import threading


class ExecutorHandler(ClassHandler):
  '''
  The :class:`ExecutorHandler` class gives a single entrypoint to interact with
  the ``concurrent.futures`` executor class.
  '''

  def _connect_backend(self):
    '''
    Loads the executor backend's base module, given either a fully qualified
    compute backend name, or a partial (``terra.executor.{partial}.executor``),
    and then returns a connection to the backend

    Parameters
    ----------
    self._override_type : :class:`str`, optional
        If not ``None``, override the name of the backend to load.
    '''

    print('SGR - _connect_backend')

    backend_name = self._override_type

    if backend_name is None:
      backend_name = settings.executor.type

    if backend_name == "DummyExecutor":
      from terra.executor.dummy import DummyExecutor
      return DummyExecutor
    elif backend_name == "SyncExecutor":
      from terra.executor.sync import SyncExecutor
      return SyncExecutor
    elif backend_name == "ThreadPoolExecutor":
      return concurrent.futures.ThreadPoolExecutor
    elif backend_name == "ProcessPoolExecutor":
      return concurrent.futures.ProcessPoolExecutor
    elif backend_name == "CeleryExecutor":
      import terra.executor.celery
      return terra.executor.celery.CeleryExecutor
    else:
      module_name = backend_name.rsplit('.', 1)
      module = import_module(f'{module_name[0]}')
      return getattr(module, module_name[1])

  def configuration_map(self, service_info):
    if not hasattr(self._connection, 'configuration_map'):
      # Default behavior
      return []
    # else call the class specific implementation
    return self._connection.configuration_map(service_info)

  def reconfigure_logger(self, logging_handler):
    # The default logging handler is a StreamHandler. This will reconfigure its
    # output stream

    print("SGR - reconfigure logging")
    return

    log_file = os.path.join(settings.processing_dir,
                            terra.logger._logs.default_log_prefix)

    # if not os.path.samefile(log_file, self._log_file.name):
    if log_file != self._log_file.name:
      os.makedirs(settings.processing_dir, exist_ok=True)
      self._log_file.close()
      self._log_file = open(log_file, 'a')

    #self._reconfigure_logger(logging_handler)

  def _reconfigure_logger(self, logging_handler):
    # FIXME no idea how to reset this
    # setup the logging when a task is reconfigured; e.g., changing logging
    # level or hostname

    if settings.terra.zone == 'runner' or settings.terra.zone == 'task':
      print("SGR - reconfigure runner/task logging")

      # when the celery task is done, its logger is automatically reconfigured;
      # use that opportunity to close the stream
      #self._socket_handler.close()

  def configure_logger(self):
    # ThreadPoolExecutor will work just fine with a normal StreamHandler

    try:
      return self._configure_logger()
      # REVIEW this may not be needed anymore. it also is in the
      # Justfile and docker-compose.yml
      # In CeleryPoolExecutor, use the Celery logger.
      # Use this to determine if main process or just a worker?
      # https://stackoverflow.com/a/45022530/4166604
      # Use TERRA_IS_CELERY_WORKER
    except AttributeError:
      # Setup log file for use in configure
      self._log_file = os.path.join(settings.processing_dir,
                                    terra.logger._logs.default_log_prefix)
      os.makedirs(settings.processing_dir, exist_ok=True)
      self._log_file = open(self._log_file, 'a')

      self._logging_handler = logging.StreamHandler(stream=self._log_file)
      return self._logging_handler

      # TODO: ProcessPool - Log server

  def _configure_logger(self):
    # FIXME don't hardcode hostname/port
    self._hostname = 'kanade' # settings.terra.celery.hostname
    self._port = logging.handlers.DEFAULT_TCP_LOGGING_PORT # settings.terra.celery.logging_port

    if settings.terra.zone == 'controller':
      print("SGR - setting up controller logging")

      # setup the listener
      self.tcp_logging_server = LogRecordSocketReceiver(self._hostname, self._port)
      print('About to start TCP server...')

      lp = threading.Thread(target=self.tcp_logging_server.serve_until_stopped)
      lp.setDaemon(True)
      # FIXME can't actually handle a log message until logging is done configuring
      lp.start()
      # TODO do we need to join
      #lp.join()

      raise AttributeError
    elif settings.terra.zone == 'runner' or settings.terra.zone == 'task':
      print("SGR - setting up runner/task logging")

      self._socket_handler = logging.handlers.SocketHandler(self._hostname,
          self._port)

      # TODO would probably be good to also setup another handler to log to disk

      # TODO don't bother with a formatter, since a socket handler sends the event
      # as an unformatted pickle

      return self._socket_handler
    elif settings.terra.zone == 'task_controller':
      raise AttributeError
    else:
      assert False, 'unknown zone: ' + settings.terra.zone

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


Executor = ExecutorHandler()
'''ExecutorHandler: The executor handler that all services will be interfacing
with when running parallel computation tasks.
'''
