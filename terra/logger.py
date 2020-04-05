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
according to the :ref:`settings_logging`, named ``terra_log`` in your
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

See :ref:`settings_logging` for how to customize the logger

Usage
-----

To use the logger, in any module always:

```
from terra.logging import get_logger
logger = get_logger(__name__)
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

from terra.core.exceptions import ImproperlyConfigured

from logging import (
  CRITICAL, ERROR, INFO, FATAL, WARN, WARNING, NOTSET,
  getLogger, _acquireLock, _releaseLock, currentframe,
  _srcfile as logging_srcfile, Logger as Logger_original
)


__all__ = ['getLogger', 'CRITICAL', 'ERROR', 'INFO', 'FATAL', 'WARN',
           'WARNING', 'NOTSET', 'DEBUG1', 'DEBUG2', 'DEBUG3', 'Logger']


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


class _SetupTerraLogger():
  '''
  A simple logger class used internally to configure the logger before and
  after :data:`terra.settings` is configured
  '''
  default_formatter = logging.Formatter('%(asctime)s (preconfig) : '
                                        '%(levelname)s - %(message)s')
  default_stderr_handler_level = logging.WARNING
  default_tmp_prefix = "terra_initial_tmp_"
  default_log_prefix = "terra_log"

  def __init__(self):
    self._configured = False
    self.root_logger = logging.getLogger(None)
    self.root_logger.setLevel(0)

    # stream -> stderr
    self.stderr_handler = logging.StreamHandler(sys.stderr)
    self.stderr_handler.setLevel(self.default_stderr_handler_level)
    self.stderr_handler.setFormatter(self.default_formatter)
    self.root_logger.addHandler(self.stderr_handler)

    # Set up temporary file logger
    self.tmp_file = tempfile.NamedTemporaryFile(mode="w+",
                                                prefix=self.default_tmp_prefix,
                                                delete=False)
    self.tmp_handler = logging.StreamHandler(stream=self.tmp_file)
    self.tmp_handler.setLevel(0)
    self.tmp_handler.setFormatter(self.default_formatter)
    self.root_logger.addHandler(self.tmp_handler)

    # setup Buffers to use for replay after configure
    self.preconfig_stderr_handler = \
        logging.handlers.MemoryHandler(capacity=1000)
    self.preconfig_stderr_handler.setLevel(0)
    self.preconfig_stderr_handler.setFormatter(self.default_formatter)
    self.root_logger.addHandler(self.preconfig_stderr_handler)

    self.preconfig_main_log_handler = \
        logging.handlers.MemoryHandler(capacity=1000)
    self.preconfig_main_log_handler.setLevel(0)
    self.preconfig_main_log_handler.setFormatter(self.default_formatter)
    self.root_logger.addHandler(self.preconfig_main_log_handler)

    # Replace the exception hook with our exception handler
    self.setup_logging_exception_hook()
    self.setup_logging_ipython_exception_hook()

    # This will use the default logger, not my adaptor, and fail on hostname
    # captureWarnings(True)
    # Just do what captureWarnings does, but manually
    global _warnings_showwarning
    _warnings_showwarning = warnings.showwarning
    warnings.showwarning = handle_warning

    # Enable warnings to default
    warnings.simplefilter('default')

  def setup_logging_exception_hook(self):
    '''
    Setup logging of uncaught exceptions

    MITM insert an error logging call on all uncaught exceptions. Should only
    be called once, or else errors will be logged multiple times
    '''

    # Make a copy of the original hook so the inner function can call it
    original_hook = sys.excepthook

    # https://stackoverflow.com/a/16993115/4166604
    def handle_exception(exc_type, exc_value, exc_traceback):
      # Try catch here because I want to make sure the original hook is called
      try:
        logger.error("Uncaught exception",
                     exc_info=(exc_type, exc_value, exc_traceback))
      except Exception:  # pragma: no cover
        print('There was an exception logging in the execpetion handler!')
        traceback.print_exc()

      return original_hook(exc_type, exc_value, exc_traceback)

    # Replace the hook
    sys.excepthook = handle_exception

  # https://stackoverflow.com/a/49176714/4166604
  def setup_logging_ipython_exception_hook(self):
    '''
    Setup logging of uncaught exceptions in ipython

    MITM insert an error logging call on all uncaught exceptions. Should only
    be called once, or else errors will be logged multiple times

    If IPython cannot be imported, nothing happens.
    '''
    try:
      import warnings
      with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        from IPython.core.interactiveshell import InteractiveShell

      original_exception = InteractiveShell.showtraceback

      def handle_traceback(*args, **kwargs):  # pragma: no cover
        getLogger(__name__).error("Uncaught exception",
                                  exc_info=sys.exc_info())
        return original_exception(*args, **kwargs)

      InteractiveShell.showtraceback = handle_traceback

    except ImportError:  # pragma: no cover
      pass

  def reconfigure_logger(self, sender=None, **kwargs):
    if not self._configured:
      self.root_logger.error("It is unexpected for reconfigure_logger to be "
                             "called, without first calling configure_logger. "
                             "This is not critical, but should not happen.")

    self.set_level_and_formatter()

    # Must be imported after settings configed
    from terra.executor import Executor
    Executor.reconfigure_logger(self.main_log_handler)

  def set_level_and_formatter(self):
    from terra import settings
    formatter = logging.Formatter(fmt=settings.logging.format,
                                  datefmt=settings.logging.date_format,
                                  style=settings.logging.style)

    # Configure log level
    level = settings.logging.level
    if isinstance(level, str):
      # make level case insensitive
      level = level.upper()
    self.stderr_handler.setLevel(level)
    self.main_log_handler.setLevel(level)

    # Configure format
    self.main_log_handler.setFormatter(formatter)
    self.stderr_handler.setFormatter(formatter)

  def configure_logger(self, sender, **kwargs):
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

    # Must be imported after settings configed
    from terra.executor import Executor
    self.main_log_handler = Executor.configure_logger()

    self.set_level_and_formatter()

    # Swap some handlers
    self.root_logger.addHandler(self.main_log_handler)
    self.root_logger.removeHandler(self.preconfig_stderr_handler)
    self.root_logger.removeHandler(self.preconfig_main_log_handler)
    self.root_logger.removeHandler(self.tmp_handler)

    settings_dump = os.path.join(settings.processing_dir,
                                 datetime.now(timezone.utc).strftime(
                                     'settings_%Y_%m_%d_%H_%M_%S_%f.json'))
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
    # second time anyways. This applys to stderr only, not the log file
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
    os.unlink(self.tmp_file.name)
    self.tmp_file = None

    self._configured = True


extra_logger_variables = {'hostname': platform.node()}
'''dict: Extra logger variables that can be reference in log messages'''


class Logger(Logger_original):
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

  # Define _log instead of logger adapter, this works better (setLoggerClass)
  # https://stackoverflow.com/a/28050837/4166604
  def _log(self, *args, **kwargs):
    kwargs['extra'] = extra_logger_variables
    return super()._log(*args, **kwargs)

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


_srcfiles = (logging_srcfile,
             os.path.normcase(Logger.debug1.__code__.co_filename))


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

logging.addLevelName(DEBUG1, "DEBUG1")
logging.addLevelName(DEBUG2, "DEBUG2")
logging.addLevelName(DEBUG3, "DEBUG3")

logging.setLoggerClass(Logger)

# Get the logger here, AFTER all the changes to the logger class
logger = getLogger(__name__)

# Disable log setup for unittests. Can't use settings here ;)
if os.environ.get('TERRA_UNITTEST', None) != "1":  # pragma: no cover
  # Must be import signal after getLogger is defined... Currently this is
  # imported from logger. But if a custom getLogger is defined eventually, it
  # will need to be defined before importing terra.core.signals.
  import terra.core.signals

  # Configure logging (pre configure)
  _logs = _SetupTerraLogger()

  # register post_configure with settings
  terra.core.signals.post_settings_configured.connect(_logs.configure_logger)

  # Handle a "with" settings context manager
  terra.core.signals.post_settings_context.connect(_logs.reconfigure_logger)
