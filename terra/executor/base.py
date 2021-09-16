from concurrent.futures import Future, Executor

from terra.logger import getLogger
logger = getLogger(__name__)


class BaseExecutor(Executor):
  # Most Executors' loggers are already configured because they were forked
  # from a runner that was configured.
  #
  # We allow most of these Executors to keep the compute's logging behavior.
  # In particular, the Executor continues to log directly to the master
  # controller's stderr (in addition to a SocketHandler monitored by the
  # master controller).
  #
  # NOTE While the messages logged to the stderr may be interleaved with
  # messages from other tasks, this has not been a problem yet. If it becomes
  # one, we can revisit this. As noted, the Executors and runners also send
  # messages (via a SocketHandler) to the master controller, which receives
  # them synchronously and logs them to file.
  #
  # Currently, the CeleryExecutor is the only Executor that is not forked from
  # a runner; these tasks are forked off of the celery process. The loggers for
  # these tasks must be reconfigured once they are started up and the settings
  # are avaliable. Similarly, any additional Executors that need custom behavior
  # must also be configured/reconfigured appropriately.

  multiprocess = False

  @staticmethod
  def configure_logger(sender, **kwargs):
    pass

  @staticmethod
  def reconfigure_logger(sender, **kwargs):
    pass


class BaseFuture(Future):
  pass
