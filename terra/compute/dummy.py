from terra.compute.base import BaseCompute, BaseService
from terra.logger import getLogger
logger = getLogger(__name__)


class Compute(BaseCompute):
  '''
  Dummy computing model. Prints messages instead of running any actual
  services
  '''

  def createService(self, service_info):
    logger.info("Create: " + str(service_info))

  def startService(self, service_info):
    logger.info("Start: " + str(service_info))

  def runService(self, service_info):
    logger.info("Run: " + str(service_info))
    super().runService(service_info)

  def stopService(self, service_info):
    logger.info("Stop: " + str(service_info))

  def removeService(self, service_info):
    logger.info("Remove: " + str(service_info))


class Service(BaseService):
  '''
  Dummy service class, prints pre_run and post_run steps
  '''

  def __init__(self):
    super().__init__()
    logger.info(f'Created on {str(self)}')

  def pre_run(self):
    logger.info(f'Pre run: {str(self)}')

  def post_run(self):
    logger.info(f'Post run: {str(self)}')
