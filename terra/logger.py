import logging.handlers
import sys
import tempfile
import threading
import os

from logging import (
  CRITICAL, ERROR, INFO, FATAL, WARN, WARNING, NOTSET, getLogger
)
# Must be imported after getLogger is defined... Currently this is imported
# from logger
from terra.core.signals import post_settings_configured


__all__ = ['getLogger', 'CRITICAL', 'ERROR', 'INFO', 'FATAL', 'WARN',
           'WARNING', 'NOTSET', 'DEBUG1', 'DEBUG2', 'DEBUG3']


class AlreadyConfigured(Exception):
  pass


class SetupTerraLogger():
  '''
  A Simple logger class to configure the logger before and after configuration
  '''
  default_formatter = logging.Formatter('%(asctime)s : %(levelname)s - %(message)s')
  default_stderr_handler_level = logging.ERROR
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
    Configure the logger after settings have been read in
    '''

    from terra import settings

    if self._configured:
      self.root_logger.error("Configure logger called twice, this is "
                             "unexpected")
      raise AlreadyConfigured()

    formatter = logging.Formatter(fmt=settings.logging.format,
                                  datefmt=settings.logging.date_format,
                                  style=settings.logging.style)

    # Setup log file for use in configure
    self.log_file = tempfile.NamedTemporaryFile(mode="w+",
                                                prefix=self.default_log_prefix,
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
  def debug1(self, msg, *args, **kwargs):
    if self.isEnabledFor(DEBUG1):
      self._log(DEBUG1, msg, args, **kwargs)
  def debug2(self, msg, *args, **kwargs):
    if self.isEnabledFor(DEBUG2):
      self._log(DEBUG2, msg, args, **kwargs)
  def debug3(self, msg, *args, **kwargs):
    if self.isEnabledFor(DEBUG3):
      self._log(DEBUG3, msg, args, **kwargs)


DEBUG1 = 10
DEBUG2 = 9
DEBUG3 = 8

logging.setLoggerClass(Logger)

logging.addLevelName(DEBUG1, "DEBUG1")
logging.addLevelName(DEBUG2, "DEBUG2")
logging.addLevelName(DEBUG3, "DEBUG3")

_logs = SetupTerraLogger()

post_settings_configured.connect(_logs.configure_logger)

# register configure with settings