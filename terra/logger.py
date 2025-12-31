'''
The logging module for all of terra apps.

Whether a part of terra core or apps, cli, workflow, service, task, all modules
should import :mod:`terra.logger` to output all messages to user and developer.

Logging, like everything is configured by :data:`terra.settings`. Before the
:data:`terra.settings` is configured, the logger is setup to create an initial
temporary log file in your systems temporary directory with the prefix
``terra_initial_tmp_XXXXXXXX`` (Where ``X`` are random characters). This
initial log file will capture all levels of log messages (Down to
:data:`DEBUG3`). During this time, stdout will also emit message at the default
level of :data:`logging.WARNING`.

This initial file in only useful in extremely rare circumstances where terra
crashes before it is even configured.

After the :data:`terra.settings` are
:data:`initialized<terra.core.signals.post_settings_configured>`, the
``terra_initial_tmp_XXXXXXXX`` file is removed, and another log file is used
according to the :ref:`settings-logging`, named ``terra_log`` in your
:data:`terra.core.settings.processing_dir`. The ``terra_log`` file is appended
to if it already exists.

All messages that are emitted before :data:`terra.settings` is configured are
then replayed for the newly configured logger handlers so that any messages of
interest will be seen on stdout and saved in the final log file.

.. note::

    In the rare case any :data:`logging.WARNING` or above messages that appear
    before :data:`terra.settings` is configured, they may be display a second
    time on ``stdout``. This repetition only occurs on ``stdout`` and is
    expected

See :ref:`settings-logging` for how to customize the logger

Usage
-----

To use the logger, in any module always:

```
from terra.logging import getLogger
logger = getLogger(__name__)
```

And then use the ``logger`` object anywhere in the module. This logger is a
python :mod:`logging` logger with the following extra configuration

* Added `debug1`, `debug2`, and `debug3` levels (with `debug3` being the most
  verbose)
* `debug` is really `debug1`
* `debug3` is best used for debugging math in an algorithm
* `debug2` is best used for more verbose statements used only for development
* `debug1` is best used for verbose statements used when running
* All logging level variables exist in :mod:`terra.logger`: ``CRITICAL``,
  ``WARN``, ``DEBUG2``, etc...
'''

import logging.handlers
import sys
import tempfile
import platform
import os
import traceback
import io
import warnings
from datetime import datetime, timezone
import socket
import socketserver
import struct
import select
import pickle
import atexit
from collections import deque
from threading import Event

import terra
from terra.core.exceptions import (
  ImproperlyConfigured, setup_logging_exception_hook,
  setup_logging_ipython_exception_hook
)
# Do not import terra.settings or terra.signals here, or any module that
# imports them

from logging import (
  CRITICAL, ERROR, INFO, FATAL, WARN, WARNING, NOTSET, Filter,
  getLogger, _acquireLock, _releaseLock, currentframe, Formatter,
  _srcfile as logging_srcfile, Logger as Logger_original
)


__all__ = ['getLogger', 'CRITICAL', 'ERROR', 'INFO', 'FATAL', 'WARN',
           'WARNING', 'NOTSET', 'DEBUG1', 'DEBUG2', 'DEBUG3', 'DEBUG4',
           'Logger']


class RingMemoryHandler(logging.handlers.MemoryHandler):
  '''
  A Ring Memory Handler that keeps the last n messages of a certain severity.

  Since this is designed for terra's settings, it starts off as a normal
  :py:class:`logging.handlers.MemoryHandler`, and records all the messages.
  Once settings have initialized, it swaps over to a deque for the buffer,
  and only keeps the last ``self.capacity`` of ``self.level`` or higher.
  '''

  def shouldFlush(self, record):
    # Disable auto flushing. We only want to flush at the end with the report
    return False

  def activate_ring(self):
    '''
    Once ``self.capacity`` and ``setLevel`` are set, call ``activate_ring`` to
    enable the ring buffer. This is delayed from ``__init__`` so that you can
    capture all the logs before you know the max severity and count; then
    keep only the last ``self.capacity`` messages of severity ``self.level`` or
    higher.
    '''
    with self.lock:
      self.buffer = deque((b for b in self.buffer if b.levelno >= self.level),
                          maxlen=self.capacity)


class HandlerLoggingContext(object):
  '''
  A context Manager for swapping out logging handlers
  '''

  def __init__(self, logger, handlers):
    '''
    Arguments
    ---------
    logger:
        The logger to swap handlers on
    handlers: list
        List of handles to set the logger to
    '''
    self.handlers = handlers
    if isinstance(logger, logging.LoggerAdapter):
      self.logger = logger.logger
    else:
      self.logger = logger

  def __enter__(self):
    try:
      _acquireLock()
      self.old_handlers = self.logger.handlers
      self.logger.handlers = self.handlers
    finally:
      _releaseLock()

  def __exit__(self, et, ev, tb):
    try:
      _acquireLock()
      self.logger.handlers = self.old_handlers
    finally:
      _releaseLock()
    # implicit return of None => don't swallow exceptions


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
    logger = getLogger(name)
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

  def __init__(self,
               address=('localhost',
                        logging.handlers.DEFAULT_TCP_LOGGING_PORT),
               family='AF_INET',
               handler=LogRecordStreamHandler):

    if family == 'AF_INET':
      self.address_family = socket.AF_INET
    elif family == 'AF_INET6':
      self.address_family = socket.AF_INET6
    elif family == 'AF_UNIX':
      self.address_family = socket.AF_UNIX
    elif family == 'AF_PIPE':
      self.address_family = socket.AF_PIPE
    else:
      raise ValueError(f'Invalid value of socket family: {family}. Currently '
                       'only AF_INET, AF_INET6, AF_UNIX and AF_PIPE are '
                       'supported')
    socketserver.ThreadingTCPServer.__init__(self, address, handler)

    # Auto delete file socket, or else it'll cause a bind error next time, plus
    # it looks ugly to leave these around
    if self.address_family == getattr(socket, 'AF_UNIX', None):
      atexit.register(cleanup_named_socket, self.server_address)

    self.ready = False
    self.timeout = 0.1
    self.logname = None

  def serve_forever(self):
    self.ready = True
    super().serve_forever()
    self.ready = False


def cleanup_named_socket(server_address):
  try:
    os.remove(server_address)
  except Exception:
    pass


class _SetupTerraLogger():
  '''
  A simple logger class used internally to configure the logger before and
  after :data:`terra.settings` is configured
  '''
  default_formatter = logging.Formatter('%(asctime)s (%(hostname)s:%(zone)s) :'
                                        ' %(levelname)s - %(filename)s -'
                                        ' %(message)s')
  default_stderr_handler_level = logging.WARNING
  default_tmp_prefix = "terra_initial_tmp_"

  def __init__(self):
    self._configured = False

    # This must always use logging's getLogger. If a custom Terra getLogger is
    # ever defined, don't use it to get the root logger
    self.root_logger = logging.getLogger(None)
    self.root_logger.setLevel(0)
    # Add the Terra filter to the rootlogger, so that it gets the same extra
    # args any other terra.logger.Logger would get
    self.root_logger.addFilter(TerraAddFilter())

    # In cases where getLogger is called before _SetupTerraLogger, this will
    # patch all the loggers in the manager, to have have TerraAddFilter. This
    # will solve the KeyError: 'hostname' and 'zone' issue that sometimes pops
    # up.
    for _logger in logging.Logger.manager.loggerDict.values():
      if isinstance(_logger, logging.PlaceHolder):
        continue
      if not any(isinstance(filter, TerraAddFilter)
                 for filter in _logger.filters):
        _logger.addFilter(TerraAddFilter())

    # stream -> stderr
    self.stderr_handler = logging.StreamHandler(sys.stderr)
    self.stderr_handler.setLevel(self.default_stderr_handler_level)
    self.stderr_handler.setFormatter(self.default_formatter)
    self.stderr_handler.addFilter(StdErrFilter())
    self.root_logger.addHandler(self.stderr_handler)

    # A buffer that prints at the end to generate a report
    self.report_buffer = RingMemoryHandler(100)  # capacity doesn't matter here
    self.report_buffer.setLevel(0)
    self.report_buffer.setFormatter(self.default_formatter)
    self.report_buffer.addFilter(StdErrFilter())
    self.root_logger.addHandler(self.report_buffer)
    atexit.register(self.print_log_report)

    # Set up temporary file logger
    if os.environ.get('TERRA_DISABLE_TERRA_LOG') != '1':
      self.tmp_file = tempfile.NamedTemporaryFile(
          mode="w+", prefix=self.default_tmp_prefix, delete=False)
    else:
      self.tmp_file = open(os.devnull, mode='w+')
    self.tmp_handler = logging.StreamHandler(stream=self.tmp_file)
    self.tmp_handler.setLevel(0)
    self.tmp_handler.setFormatter(self.default_formatter)
    self.root_logger.addHandler(self.tmp_handler)

    atexit.register(self.cleanup_temp)

    # setup Buffers to use for replay after configure
    self.preconfig_stderr_handler = \
        logging.handlers.MemoryHandler(capacity=1000)
    self.preconfig_stderr_handler.setLevel(0)
    self.preconfig_stderr_handler.setFormatter(self.default_formatter)
    self.preconfig_stderr_handler.addFilter(StdErrFilter())
    self.root_logger.addHandler(self.preconfig_stderr_handler)

    self.preconfig_main_log_handler = \
        logging.handlers.MemoryHandler(capacity=1000)
    self.preconfig_main_log_handler.setLevel(0)
    self.preconfig_main_log_handler.setFormatter(self.default_formatter)
    self.root_logger.addHandler(self.preconfig_main_log_handler)

    # Replace the exception hook with our exception handler
    setup_logging_exception_hook()
    setup_logging_ipython_exception_hook()

    # This will use the default logger, not my adaptor, and fail on hostname
    # captureWarnings(True)
    # Just do what captureWarnings does, but manually
    global _warnings_showwarning
    _warnings_showwarning = warnings.showwarning
    warnings.showwarning = handle_warning

    # Enable warnings to default, append this to the end of the filter list,
    # so that any filters set elsewhere are not overridden by the behavior
    warnings.simplefilter('default', append=True)
    # Disable known warnings that there's nothing to be done about.
    for module in ('yaml', 'celery.app.amqp'):
      warnings.filterwarnings("ignore",
                              category=DeprecationWarning, module=module,
                              message="Using or importing the ABCs")
    warnings.filterwarnings("ignore",
                            category=DeprecationWarning, module='osgeo',
                            message="the imp module is deprecated")

  @property
  def main_log_handler(self):
    try:
      return self.__main_log_handler
    except AttributeError:
      raise AttributeError("'_logs' has no 'main_log_handler'. An executor "
                           "class' 'configure_logger' method should setup a "
                           "'main_log_handler'.")

  @main_log_handler.setter
  def main_log_handler(self, value):
    self.__main_log_handler = value

  def set_level_and_formatter(self):
    from terra import settings
    formatter = logging.Formatter(fmt=settings.logging.format,
                                  datefmt=settings.logging.date_format,
                                  style=settings.logging.style)

    stderr_formatter = ColorFormatter(fmt=settings.logging.format,
                                      datefmt=settings.logging.date_format,
                                      style=settings.logging.style)

    # Configure log level
    level = settings.logging.level
    if isinstance(level, str):
      # make level case insensitive
      level = level.upper()

    if getattr(self, 'stderr_handler', None) is not None:
      self.stderr_handler.setLevel(level)
      self.stderr_handler.setFormatter(stderr_formatter)

    if getattr(self, 'main_log_handler', None) is not None:
      self.main_log_handler.setLevel(level)
      self.main_log_handler.setFormatter(formatter)

    if getattr(self, 'report_buffer', None) is not None:
      self.report_buffer.setLevel(settings.logging.severe_level)
      self.report_buffer.capacity = settings.logging.severe_buffer_length
      self.report_buffer.activate_ring()

    # This hides the messages that spams the screen:
    # "pipbox received method enable_events() [reply_to:None ticket:None]"
    # This is the only debug message in all of kombu.pidbox, so this is pretty
    # safe to do, similar for celery.bootsteps and filelock
    _demoteLevel(('kombu.pidbox', 'celery.bootsteps', 'filelock'),
                 DEBUG1, DEBUG4)

  def configure_logger(self, sender=None, signal=None, **kwargs):
    '''
    Call back function to configure the logger after settings have been
    configured
    '''

    from terra import settings
    from terra.core.settings import TerraJSONEncoder

    if self._configured:
      self.root_logger.error("Configure logger called twice, this is "
                             "unexpected")
      raise ImproperlyConfigured()

    # This sends a signal to the current Executor type, which has already been
    # imported at the end of LazySettings.configure. We don't import Executor
    # here to reduce the concerns of this module
    import terra.core.signals
    terra.core.signals.logger_configure.send(sender=self, **kwargs)
    self.set_level_and_formatter()

    # Now that the real logger has been set up, swap some handlers
    self.root_logger.removeHandler(self.preconfig_stderr_handler)
    self.root_logger.removeHandler(self.preconfig_main_log_handler)
    self.root_logger.removeHandler(self.tmp_handler)

    if not settings.terra.disable_settings_dump:
      settings_dump_file = ('settings_%Y_%m_%d_%H_%M_%S_%f_'
                            f'{settings.terra.zone}_')
      if settings.terra.zone == 'runner':
        settings_dump_file += f'{settings.terra.current_service}_'
      settings_dump_file += f'{settings.terra.uuid}.json'

      os.makedirs(settings.settings_dir, exist_ok=True)
      settings_dump = os.path.join(
          settings.settings_dir,
          datetime.now(timezone.utc).strftime(settings_dump_file))
      with open(settings_dump, 'w') as fid:
        fid.write(TerraJSONEncoder.dumps(settings, indent=2))

    # filter the stderr buffer
    self.preconfig_stderr_handler.buffer = \
        [x for x in self.preconfig_stderr_handler.buffer
         if (x.levelno >= self.stderr_handler.level)]
    # Use this if statement if you want to prevent repeating any critical/error
    # level messages. This is probably not necessary because error/critical
    # messages before configure should be rare, and are probably worth
    # repeating. Repeating is the only way to get them formatted right the
    # second time anyways. This applies to stderr only, not the log file
    #                        if (x.levelno >= level)] and
    #                           (x.levelno < default_stderr_handler_level)]

    # Filter file buffer. Never remove default_stderr_handler_level message,
    # they won't be in the new output file
    self.preconfig_main_log_handler.buffer = \
        [x for x in self.preconfig_main_log_handler.buffer
         if (x.levelno >= self.main_log_handler.level)]

    # Flush the buffers
    self.preconfig_stderr_handler.setTarget(self.stderr_handler)
    self.preconfig_stderr_handler.flush()
    self.preconfig_stderr_handler = None
    self.preconfig_main_log_handler.setTarget(self.main_log_handler)
    self.preconfig_main_log_handler.flush()
    self.preconfig_main_log_handler = None
    self.tmp_handler = None

    # Remove the temporary file now that you are done with it
    self.tmp_file.close()
    if os.path.exists(self.tmp_file.name) and self.tmp_file.name != os.devnull:
      os.unlink(self.tmp_file.name)
    self.tmp_file = None

    self._configured = True

  def reconfigure_logger(self, sender=None, signal=None, **kwargs):
    if not self._configured:
      self.root_logger.error("It is unexpected for reconfigure_logger to be "
                             "called, without first calling configure_logger. "
                             "This is not critical, but should not happen.")

    # This sends a signal to the current Executor type, which has already been
    # imported at the end of LazySettings.configure. We don't import Executor
    # here to reduce the concerns of this module
    import terra.core.signals
    terra.core.signals.logger_reconfigure.send(sender=self, **kwargs)

    self.set_level_and_formatter()

  def cleanup_temp(self):
    try:
      # If the file exists and was not /dev/null
      if self.tmp_file and self.tmp_file.name != os.devnull and \
         os.path.exists(self.tmp_file.name):
        if (not self.tmp_file.file.closed and self.tmp_file.tell() == 0) or \
           (self.tmp_file.file.closed
            and os.stat(self.tmp_file.name).st_size == 0):
          # if the filesize is zero, delete it. No point in littering
          os.unlink(self.tmp_file.name)
    except AttributeError:
      pass

  def print_log_report(self):
    try:
      from terra import settings
      if settings.terra.zone == 'controller':
        print('\nTerra Logging report', file=sys.stderr)
        print('====================', file=sys.stderr)
        if self.report_buffer.buffer:
          print(f'Here are the last {len(self.report_buffer.buffer)} error(s)'
                f' (max: {self.report_buffer.capacity})',
                file=sys.stderr)

          formatter = ColorFormatter(fmt=settings.logging.format,
                                     datefmt=settings.logging.date_format,
                                     style=settings.logging.style)

          report_handler = logging.StreamHandler(sys.stderr)
          report_handler.setLevel(settings.logging.severe_level)
          report_handler.setFormatter(formatter)
          report_handler.addFilter(StdErrFilter())
          self.report_buffer.setTarget(report_handler)
          self.report_buffer.flush()
        else:
          print('No severe log message, good job!', file=sys.stderr)
    except Exception:
      pass


class TerraAddFilter(Filter):
  def filter(self, record):
    if not hasattr(record, 'hostname'):
      record.hostname = platform.node()
    if not hasattr(record, 'zone'):
      try:
        if terra.settings.configured:
          record.zone = terra.settings.terra.zone
        else:
          record.zone = 'preconfig'
      except BaseException:
        record.zone = 'preconfig'
    return True


class StdErrFilter(Filter):
  def filter(self, record):
    return not getattr(record, 'skip_stderr', False)


class SkipStdErrAddFilter(Filter):
  def filter(self, record):
    record.skip_stderr = getattr(record, 'skip_stderr', True)
    return True


class ColorFormatter(Formatter):
  use_color = True

  def format(self, record):
    if self.use_color:
      zone = record.__dict__.get('zone', 'preconfig')
      if zone == "preconfig":
        record.__dict__['zone'] = '\033[33mpreconfig\033[0m'
      elif zone == "controller":
        record.__dict__['zone'] = '\033[32mcontroller\033[0m'
      elif zone == "runner":
        record.__dict__['zone'] = '\033[35mrunner\033[0m'
      elif zone == "task":
        record.__dict__['zone'] = '\033[34mtask\033[0m'
      else:
        record.__dict__['zone'] = f'\033[31m{record.__dict__["zone"]}\033[0m'

      msg = super().format(record)
      record.__dict__['zone'] = zone
      return msg
    else:
      return super().format(record)


class Logger(Logger_original):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # I like https://stackoverflow.com/a/17558764/4166604 better than
    # https://stackoverflow.com/a/28050837/4166604, it has the ability to add
    # logic/function calls, if I so desire
    self.addFilter(TerraAddFilter())

  def findCaller(self, stack_info=False, stacklevel=1):
    """
    Find the stack frame of the caller so that we can note the source
    file name, line number and function name.
    """
    f = currentframe()
    # On some versions of IronPython, currentframe() returns None if
    # IronPython isn't run with -X:Frames.
    if f is not None:
      f = f.f_back
    orig_f = f
    while f and stacklevel > 1:
      f = f.f_back
      stacklevel -= 1
    if not f:
      f = orig_f
    rv = "(unknown file)", 0, "(unknown function)", None
    while hasattr(f, "f_code"):
      co = f.f_code
      filename = os.path.normcase(co.co_filename)
      # I have to fix this line to be smarter
      if filename in _srcfiles:
        f = f.f_back
        continue
      sinfo = None
      if stack_info:
        sio = io.StringIO()
        sio.write('Stack (most recent call last):\n')
        traceback.print_stack(f, file=sio)
        sinfo = sio.getvalue()
        if sinfo[-1] == '\n':
          sinfo = sinfo[:-1]
        sio.close()
      rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
      break
    return rv

  # Define _log instead of logger adapter if needed, this works better
  # (setLoggerClass) https://stackoverflow.com/a/28050837/4166604

  def debug1(self, msg, *args, **kwargs):
    '''
    Logs a message with level :data:`DEBUG1` on this logger. Same as ``debug``.
    The arguments are interpreted as for :func:`logging.debug`
    '''
    self.log(DEBUG1, msg, *args, **kwargs)

  def debug2(self, msg, *args, **kwargs):
    '''
    Logs a message with level :data:`DEBUG2` on this logger. The arguments are
    interpreted as for :func:`logging.debug`
    '''
    self.log(DEBUG2, msg, *args, **kwargs)

  def debug3(self, msg, *args, **kwargs):
    '''
    Logs a message with level :data:`DEBUG3` on this logger. The arguments are
    interpreted as for :func:`logging.debug`
    '''
    self.log(DEBUG3, msg, *args, **kwargs)

  def debug4(self, msg, *args, **kwargs):
    '''
    Logs a message with level :data:`DEBUG4` on this logger. The arguments are
    interpreted as for :func:`logging.debug`
    '''
    self.log(DEBUG4, msg, *args, **kwargs)

  fatal = logging.LoggerAdapter.critical


_warnings_showwarning = None


def handle_warning(message, category, filename, lineno, file=None, line=None):
  """
  Implementation of showwarnings which redirects to logging, which will first
  check to see if the file parameter is None. If a file is specified, it will
  delegate to the original warnings implementation of showwarning. Otherwise,
  it will call warnings.formatwarning and will log the resulting string to a
  warnings logger named "py.warnings" with level logging.WARNING.
  """

  if file is not None:  # I don't actually know how this can be not None
    if _warnings_showwarning is not None:  # pragma: no cover
      _warnings_showwarning(message, category, filename, lineno, file, line)
  else:
    s = warnings.formatwarning(message, category, filename, lineno, line)
    logger = getLogger("py.warnings")
    logger.warning("%s", s)


# Ordinarily we would use __file__ for this, but frozen modules don't always
# have __file__ set, for some reason (see Issue CPython#21736). Thus, we get
# the filename from a handy code object from a function defined in this
# module. (There's no particular reason for picking debug1.)
_srcfiles = (logging_srcfile,
             os.path.normcase(Logger.debug1.__code__.co_filename),
             warnings.showwarning.__code__.co_filename)


DEBUG1 = 10
'''
Debug level one. Same as the original :data:`logging.DEBUG` level, but now
called :data:`DEBUG1`.

Should be used for general runtime debug messages that would be useful for
users to see
'''
DEBUG2 = 9
'''
Debug level two, more verbose.

Should be used for general development debug messages that would be useful for
developer to see when debugging
'''
DEBUG3 = 8
'''
Debug level three, even more verbose.

Should be used for more specific development debug messages, such as math
output used to debug algorithms
'''

DEBUG4 = 7
'''
Debug level four, even more verbose.

Should be used for spamming the screen
'''


logging.addLevelName(DEBUG1, "DEBUG1")
logging.addLevelName(DEBUG2, "DEBUG2")
logging.addLevelName(DEBUG3, "DEBUG3")
logging.addLevelName(DEBUG4, "DEBUG4")

logging.setLoggerClass(Logger)

# Get the logger here, AFTER all the changes to the logger class
logger = getLogger(__name__)


def _checkLevel(log_level):
  '''
  Translate ``log_level`` to integer.
  '''
  if isinstance(log_level, str):
    log_level = log_level.upper()
  return logging._checkLevel(log_level)


def _demoteLevel(package_names, from_level=DEBUG1, to_level=DEBUG4):
  '''
  Demote logging level for specific packages, disabling ``from_level`` log
  messages unless ``terra.settings.logging.level > to_level``.

  Arguments
  ---------
  package_names : :obj:`list` of :obj:`str`
    List of package names
  from_level
    Log level to be demoted, default ``DEBUG1``
  to_level
    New log level, default ``DEBUG4``

  '''
  from terra import settings
  log_level = _checkLevel(settings.logging.level)

  if to_level < log_level and log_level <= from_level:
    for package_name in package_names:
      getLogger(package_name).setLevel(from_level + 1)


def _setup_terra_logger():
  # Must be import signal after getLogger is defined... Currently this is
  # imported from logger. But if a custom getLogger is defined eventually, it
  # will need to be defined before importing terra.core.signals.
  import terra.core.signals

  # Configure logging (pre configure)
  logs = _SetupTerraLogger()

  # Register post_configure with settings
  terra.core.signals.post_settings_configured.connect(logs.configure_logger)

  # Handle a "with" settings context manager
  terra.core.signals.post_settings_context.connect(logs.reconfigure_logger)

  return logs


# Disable log setup for unittests. Can't use settings here ;)
if os.environ.get('TERRA_UNITTEST', None) != "1":  # pragma: no cover
  _logs = _setup_terra_logger()
