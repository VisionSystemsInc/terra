from terra import settings
from terra.compute.docker import (
  Service as DockerService,
  Compute as DockerCompute
)
from terra.compute.singularity import (
  Service as SingularityService,
  Compute as SingularityCompute
)
from terra.compute.virtualenv import (
  Service as VirtualEnvService,
  Compute as VirtualEnvCompute
)
from terra.compute.base import BaseService
from terra.core.settings import TerraJSONEncoder
from os import environ as env
import json
import os
import posixpath
from terra.logger import getLogger
logger = getLogger(__name__)


class Demo1(BaseService):
  ''' Simple Demo Service '''
  command = ['python', '-m', 'terra.tests.demo.runners.demo1']
  CONTAINER_PROCESSING_DIR = "/processing"

  def pre_run(self):
    self.add_volume(settings.processing_dir,
                    Demo1.CONTAINER_PROCESSING_DIR,
                    'rw')
    super().pre_run()


@DockerCompute.register(Demo1)
class Demo1_docker(DockerService, Demo1):
  def __init__(self):
    super().__init__()
    self.compose_files = [os.path.join(env['TERRA_TERRA_DIR'],
                                       'docker-compose-main.yml')]
    self.compose_service_name = 'terra-demo'


@VirtualEnvCompute.register(Demo1)
class Demo1_virtualenv(VirtualEnvService, Demo1):
  pass