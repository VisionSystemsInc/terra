from terra.compute.base import BaseCompute, BaseService
# from terra import settings
from terra.compute.utils import load_service
from terra.logger import getLogger
logger = getLogger(__name__)


class Compute(BaseCompute):
  '''
  Dummy computing model. Prints messages instead of running any actual
  services
  '''

  def create(self, service_class):
    logger.info("Create: " + str(load_service(service_class)))

  def start(self, service_class):
    logger.info("Start: " + str(load_service(service_class)))

  def run(self, service_class):
    service_info = load_service(service_class)
    logger.info("Run: " + str(service_info))
    service_info.pre_run()
    self.create(service_class)
    self.start(service_class)
    service_info.post_run()

  def stop(self, service_class):
    logger.info("Stop: " + str(load_service(service_class)))

  def remove(self, service_class):
    logger.info("Remove: " + str(load_service(service_class)))


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
