import os
from os import environ as env

# Terra settings
from terra import settings

# Terra compute architectures
from terra.compute.virtualenv import (
  Compute as VenvCompute
)
from terra.compute.docker import (
  Compute as DockerCompute
)
from terra.compute.singularity import (
  Compute as SingularityCompute
)

from terra.compute.base import BaseService
from terra.compute.docker import Service as DockerService
from terra.compute.container import ContainerService
from terra.compute.singularity import Service as SingularityService
from terra.compute.virtualenv import Service as VenvService

# Terra logger
from terra.logger import getLogger
logger = getLogger(__name__)


###############################################################################
#                               Generic Service                               #
###############################################################################
class Generic(BaseService):
  def __init__(self):
    self.justfile = os.path.join(env.get('TERRA_APP_DIR', '/src'), 'Justfile')

    if settings.shell:
      self.command = ['bash']
    else:
      self.command = settings.command
    super().__init__()


generic_mount_points = {
  'processing_dir': '/output',
  'source_dir': '/src'
}


class Generic_container(Generic, ContainerService):
  def __init__(self):
    self.compose_service_name = settings.compose_service

    super().__init__()

    self.add_volume(settings.processing_dir,
                    generic_mount_points['processing_dir'])

    self.add_volume_readonly(env.get('TERRA_APP_DIR', '/src'),
                             generic_mount_points['source_dir'])

    for mount in settings.mounts:
      if os.path.exists(mount[0]) and not os.path.isdir(mount[0]):
        self.add_volume(mount[0], mount[1])
      else:
        self.add_file(mount[0], mount[1])

    for mount in settings.mountsro:
      if os.path.exists(mount[0]) and not os.path.isdir(mount[0]):
        self.add_volume_readonly(mount[0], mount[1])
      else:
        self.add_file_readonly(mount[0], mount[1])


@VenvCompute.register(Generic)
class Generic_Venv(Generic, VenvService):
  pass


@DockerCompute.register(Generic)
class Generic_docker(Generic_container, DockerService):
  pass


@SingularityCompute.register(Generic)
class Generic_singular(Generic_container, SingularityService):
  pass
