from subprocess import PIPE

from terra import settings
from terra.compute.base import BaseCompute
from terra.compute.container import ContainerService
from terra.compute.utils import just
from terra.compute.base import ServiceRunFailed

from terra.logger import getLogger
logger = getLogger(__name__)

class Compute(BaseCompute):
  def run_service(self, service_info):
    '''
    Use the service class information to run the service runner in a docker
    using

    .. code-block:: bash

        just --wrap singular-compose \\
            run {service_info.compose_service_name} \\
            {service_info.command}
    '''
    pid = just("--wrap", "singular-compose",
               'run', service_info.compose_service_name,
               *(service_info.command),
               env=service_info.env)

    if pid.wait() != 0:
      raise ServiceRunFailed()
  def config_service(self, service_info, extra_compose_files=[]):
    '''
    Returns the ``singular-compose config-null`` output
    '''

    args = ["--wrap", "singular-compose",
            '-f', service_info.compose_file] + \
        sum([['-f', extra] for extra in extra_compose_files], []) + \
        ['config']

    pid = just(*args, stdout=PIPE,
               env=service_info.env)
    return pid.communicate()[0]
class Service(ContainerService):
  '''
  Base docker service class
  '''
