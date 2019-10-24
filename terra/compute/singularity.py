import os
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
    pid = just("singular-compose",
               'run', service_info.compose_service_name,
               *(service_info.command),
               env=service_info.env)

    if pid.wait() != 0:
      raise ServiceRunFailed()

  def config_service(self, service_info, extra_compose_files=[]):
    '''
    Returns the ``singular-compose config-null`` output
    '''

    args = ["singular-compose",
            '-f', service_info.compose_file] + \
        sum([['-f', extra] for extra in extra_compose_files], []) + \
        ['config-null', service_info.compose_service_name]

    pid = just(*args, stdout=PIPE,
               env=service_info.env)
    data = pid.communicate()[0]

    data = data.split(b'\0^')
    data = dict(zip([header.decode() for header in data[::2]],
                    [[chunk.decode() for chunk in group.split(b'\0.')]
                     for group in data[1::2]]))
    if 'environment' in data:
      data['environment'] = dict(zip(data['environment'][::2],
                                     data['environment'][1::2]))

    return data

  def configuration_map_service(self, service_info, extra_compose_files=[]):
    '''
    Returns the mapping of volumes from the host to the container.

    Returns
    -------
    list
        Return a list of tuple pairs [(host, remote), ... ] of the volumes
        mounted from the host to container
    '''
    # TODO: Make an OrderedDict
    volume_map = []

    config = self.config(service_info, extra_compose_files)

    volumes = config.get('volumes', [])

    for volume in volumes:
      volume = volume.split(':')
      volume_map.append((volume[0], volume[1]))

    volume_map = volume_map + service_info.volumes

    slashes = '/'
    if os.name == 'nt':
      slashes += '\\'

    # Strip trailing /'s to make things look better
    return [(volume_host.rstrip(slashes), volume_remote.rstrip(slashes))
            for volume_host, volume_remote in volume_map]


class Service(ContainerService):
  '''
  Base docker service class
  '''
