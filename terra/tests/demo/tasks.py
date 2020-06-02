from terra.task import shared_task

# Terra core
from terra.logger import getLogger
logger = getLogger(__name__)


@shared_task
def demo2(self, x, y):
  logger.critical(f"Task: {x} {y}")
  return x * y
