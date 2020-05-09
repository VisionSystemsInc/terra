import os
import logging
import logging.handlers
from concurrent.futures import Future, Executor, as_completed

import terra
from terra import settings
from terra.logger import getLogger
logger = getLogger(__name__)


class BaseExecutor(Executor):
  @staticmethod
  def configure_logger(sender, **kwargs):
    # sender is logger in this case

    # ThreadPoolExecutor will work just fine with a normal StreamHandler

    print('SGR - configure logging ' + settings.terra.zone)

  @staticmethod
  def reconfigure_logger(sender, **kwargs):
    # sender is logger in this case
    #
    # The default logging handler is a StreamHandler. This will reconfigure its
    # output stream

    print("SGR - reconfigure logging")

class BaseFuture(Future):
  pass
