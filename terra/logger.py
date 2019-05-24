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
``terra_initial_tmp_XXXXXXXX`` file is removed, and another log file is created
according to the :ref:`settings_logging`, with a ``terra_log_XXXXXXXX``
prefix in your :data:`terra.core.settings.processing_dir`.

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

* Added `debug1`, `debug2`, and `debug3` levels (with `debug3` being the most verbose)
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
import threading
import os
from terra.core.exceptions import ImproperlyConfigured

from logging import (
  CRITICAL, ERROR, INFO, FATAL, WARN, WARNING, NOTSET, getLogger
)
# Must be import signal after getLogger is defined... Currently this is imported
# from logger. But if a custom getLogger is defined eventually, it will need to
# be defined before importing terra.core.signals.
from terra.core.signals import post_settings_configured


__all__ = ['getLogger', 'CRITICAL', 'ERROR', 'INFO', 'FATAL', 'WARN',
           'WARNING', 'NOTSET', 'DEBUG1', 'DEBUG2', 'DEBUG3']


class _SetupTerraLogger():
  '''
  A simple logger class used internally to configure the logger before and
  after :data:`terra.settings` is configured
  '''
  default_formatter = logging.Formatter('%(asctime)s : %(levelname)s - %(message)s')
  default_stderr_handler_level = logging.WARNING
  default_tmp_prefix = "terra_initial_tmp_"
  default_log_prefix = "terra_log_"

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

    self.preconfig_file_handler = \
        logging.handlers.MemoryHandler(capacity=1000)
    self.preconfig_file_handler.setLevel(0)
    self.preconfig_file_handler.setFormatter(self.default_formatter)
    self.root_logger.addHandler(self.preconfig_file_handler)

  def configure_logger(self, sender, **kwargs):
    '''
    Call back function to configure the logger after settings have been
    configured
    '''

    from terra import settings

    if self._configured:
      self.root_logger.error("Configure logger called twice, this is "
                             "unexpected")
      raise ImproperlyConfigured()

    formatter = logging.Formatter(fmt=settings.logging.format,
                                  datefmt=settings.logging.date_format,
                                  style=settings.logging.style)

    # Setup log file for use in configure
    self.log_file = tempfile.NamedTemporaryFile(mode="w+",
                                                prefix=self.default_log_prefix,
                                                dir=settings.processing_dir,
                                                delete=False)
    self.file_handler = logging.StreamHandler(stream=self.log_file)

    # Configure log level
    self.stderr_handler.setLevel(settings.logging.level)
    self.file_handler.setLevel(settings.logging.level)

    # Configure format
    self.file_handler.setFormatter(formatter)
    self.stderr_handler.setFormatter(formatter)

    # Swap some handlers
    self.root_logger.addHandler(self.file_handler)
    self.root_logger.removeHandler(self.preconfig_stderr_handler)
    self.root_logger.removeHandler(self.preconfig_file_handler)
    self.root_logger.removeHandler(self.tmp_handler)


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
    self.preconfig_file_handler.buffer = \
        [x for x in self.preconfig_file_handler.buffer
         if (x.levelno >= self.file_handler.level)]

    # Flush the buffers
    self.preconfig_stderr_handler.setTarget(self.stderr_handler)
    self.preconfig_stderr_handler.flush()
    self.preconfig_stderr_handler = None
    self.preconfig_file_handler.setTarget(self.file_handler)
    self.preconfig_file_handler.flush()
    self.preconfig_file_handler = None
    self.tmp_handler = None

    # Remove the temporary file now that you are done with it
    self.tmp_file.close()
    os.unlink(self.tmp_file.name)
    self.tmp_file = None

    self._configured = True

class Logger(logging.Logger):
  '''
  Terra's :class:`logging.Logger`
  '''
  def debug1(self, msg, *args, **kwargs):
    '''
    Logs a message with level :data:`DEBUG1` on this logger. Same as ``debug``.
    The arguments are interpreted as for :func:`logging.debug`
    '''
    if self.isEnabledFor(DEBUG1):
      self._log(DEBUG1, msg, args, **kwargs)
  def debug2(self, msg, *args, **kwargs):
    '''
    Logs a message with level :data:`DEBUG2` on this logger. The arguments are
    interpreted as for :func:`logging.debug`
    '''
    if self.isEnabledFor(DEBUG2):
      self._log(DEBUG2, msg, args, **kwargs)
  def debug3(self, msg, *args, **kwargs):
    '''
    Logs a message with level :data:`DEBUG3` on this logger. The arguments are
    interpreted as for :func:`logging.debug`
    '''
    if self.isEnabledFor(DEBUG3):
      self._log(DEBUG3, msg, args, **kwargs)


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

logging.setLoggerClass(Logger)

logging.addLevelName(DEBUG1, "DEBUG1")
logging.addLevelName(DEBUG2, "DEBUG2")
logging.addLevelName(DEBUG3, "DEBUG3")

# Configure logging (pre configure)
_logs = _SetupTerraLogger()

# register post_configure with settings
post_settings_configured.connect(_logs.configure_logger)