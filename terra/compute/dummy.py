from terra.compute.base import BaseCompute, BaseService
from terra.logger import getLogger
logger = getLogger(__name__)


class Compute(BaseCompute):
  '''
  Dummy computing model. Prints messages instead of running any actual
  services
  '''

  def create_service(self, service_info):
    logger.info("Create: " + str(service_info))

  def start_service(self, service_info):
    logger.info("Start: " + str(service_info))

  def run_service(self, service_info):
    logger.info("Run: " + str(service_info))
    super().run_service(service_info)

  def stop_service(self, service_info):
    logger.info("Stop: " + str(service_info))

  def remove_service(self, service_info):
    logger.info("Remove: " + str(service_info))


class Service(BaseService):
  '''
  Dummy service class, prints pre_run and post_run steps
  '''

  def __init__(self):
    super().__init__()
    logger.info(f'Created on {str(self)}')

  def pre_run(self):
    super().pre_run()
    logger.info(f'Pre run: {str(self)}')

  def post_run(self):
    super().post_run()
    logger.info(f'Post run: {str(self)}')
