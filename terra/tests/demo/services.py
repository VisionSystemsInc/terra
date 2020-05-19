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


class Demo1(BaseService):
  ''' Simple Demo Service '''
  command = ['python', '-m', 'terra.tests.demo.runners.demo1']
  CONTAINER_PROCESSING_DIR = "/opt/test"

  def pre_run(self):
    self.add_volume(settings.processing_dir,
                    Demo1.CONTAINER_PROCESSING_DIR,
                    'rw')
    super().pre_run()


@DockerCompute.register(Demo1)
class Demo1_docker(DockerService, Demo1):
  def __init__(self):
    super().__init__()
    self.compose_files = [settings.demo.compose]
    self.compose_service_name = settings.demo.service


@SingularityCompute.register(Demo1)
class Demo1_singularity(SingularityService, Demo1):
  def __init__(self):
    super().__init__()
    self.compose_files = [settings.demo.compose]
    self.compose_service_name = settings.demo.service


@VirtualEnvCompute.register(Demo1)
class Demo1_virtualenv(VirtualEnvService, Demo1):
  pass


class Demo2(Demo1):
  ''' Simple Demo Service '''
  command = ['python', '-m', 'terra.tests.demo.runners.demo2']

@DockerCompute.register(Demo2)
class Demo2_docker(DockerService, Demo2):
  def __init__(self):
    super().__init__()
    self.compose_files = [settings.demo.compose]
    self.compose_service_name = settings.demo.service


@SingularityCompute.register(Demo2)
class Demo2_singularity(SingularityService, Demo2):
  def __init__(self):
    super().__init__()
    self.compose_files = [settings.demo.compose]
    self.compose_service_name = settings.demo.service


@VirtualEnvCompute.register(Demo2)
class Demo2_virtualenv(VirtualEnvService, Demo2):
  pass
