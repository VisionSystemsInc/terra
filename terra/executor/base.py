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
    pass

  @staticmethod
  def reconfigure_logger(sender, **kwargs):
    pass

class BaseFuture(Future):
  pass
