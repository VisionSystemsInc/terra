from terra.compute import compute

from terra.logger import getLogger
logger = getLogger(__name__)


class DemoWorkflow:
  def demonate(self):
    logger.critical('Starting demo workflow')
    compute.run('terra.tests.demo.services.Demo1')
    compute.run('terra.tests.demo.services.Demo2')
    logger.critical('Ran demo workflow')
