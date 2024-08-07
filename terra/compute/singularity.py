import os
from subprocess import PIPE

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

    # inject TERRA_SETTINGS_FILE into environment using SINGULARITYENV_*
    # https://docs.sylabs.io/guides/3.7/user-guide/environment_and_metadata.html#environment-overview
    # favor SINGULARITYENV_ for compatibility with "just singular-compose",
    # which currently requires the argument after "run" to be the service name
    service_info_env = service_info.env.copy()
    service_info_env['SINGULARITYENV_TERRA_SETTINGS_FILE'] = \
        f'{service_info_env["TERRA_SETTINGS_FILE"]}'

    command = self._get_command(service_info)

    pid = just("singular-compose",
               *sum([['--file', cf] for cf in service_info.compose_files], []),
               'run',
               service_info.compose_service_name,
               *command,
               env=service_info_env)

    if pid.wait() != 0:
      raise ServiceRunFailed(pid.returncode)

  def config_service(self, service_info):
    '''
    Returns the ``singular-compose config-null`` output
    '''

    optional_args = {}
    optional_args['justfile'] = getattr(service_info, 'justfile', None)

    args = ["singular-compose"] + \
        sum([['--file', cf] for cf in service_info.compose_files], []) + \
        ['config-null', service_info.compose_service_name]

    pid = just(*args, stdout=PIPE,
               **optional_args,
               env=service_info.env)
    data = pid.communicate()[0]

    # Split all the groups by the "header" word, null+^
    data = data.split(b'\0^')
    data = dict(zip([header.decode() for header in data[::2]],
                    # Split all the data up "data" word, null+.
                    [[chunk.decode() for chunk in group.split(b'\0.')]
                     for group in data[1::2]]))
    if 'environment' in data:
      # Environment is special, it comes in key/value pairs, zip em up.
      data['environment'] = dict(zip(data['environment'][::2],
                                     data['environment'][1::2]))

    return data

  def get_volume_map(self, config, service_info):

    # TODO: Make an OrderedDict
    volume_map = []

    volumes = config.get('volumes', [])

    for volume in volumes:
      volume = volume.split(':')
      volume_map.append((volume[0], volume[1]))

    # I think this causes duplicates, just like in the docker
    # volume_map = volume_map + service_info.volumes

    slashes = '/'
    if os.name == 'nt':
      slashes += '\\'

    # Strip trailing /'s to make things look better
    return [(volume_host.rstrip(slashes), volume_remote.rstrip(slashes))
            for volume_host, volume_remote in volume_map]

  def configuration_map_service(self, service_info):
    '''
    Returns the mapping of volumes from the host to the container.

    Returns
    -------
    list
        Return a list of tuple pairs [(host, remote), ... ] of the volumes
        mounted from the host to container
    dict
        Returns the full configuration object, that might be used for other
        configuration adaptations down the line.
    '''
    config = self.config(service_info)

    return self.get_volume_map(config, service_info)


class Service(ContainerService):
  '''
  Base singularity service class
  '''

  def __init__(self):
    super().__init__()

    # default compose file (if file exists)
    compose_file = os.path.join(self.env['TERRA_APP_DIR'],
                                'singular-compose.env')
    if os.path.isfile(compose_file):
      self.compose_files = [compose_file]
