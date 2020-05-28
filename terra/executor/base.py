from concurrent.futures import Future, Executor

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
