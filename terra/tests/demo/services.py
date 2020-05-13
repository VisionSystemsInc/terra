from terra import settings
from terra.compute.docker import (
  Service as DockerService,
  Compute as DockerCompute
)
from terra.compute.singularity import (
  Service as SingularityService,
  Compute as SingularityCompute
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
  ''' Retrieve the view angles and print them out '''


@DockerCompute.register(ViewAngle)
class ViewAngleRetrieval_docker(DockerService, ViewAngle):
  def __init__(self):
    super().__init__()

    # self.command = ['python', '-m', 'viewangle.runner_viewangle']
    self.command = ['python', '-m', 'print(12345)']

    self.compose_files = [os.path.join(env['TERRA_TERRA_DIR'],
                                       'docker-compose-main.yml')]

    self.compose_service_name = 'terra'