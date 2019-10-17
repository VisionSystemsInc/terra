import os
import posixpath
import ntpath
from os import environ as env
from subprocess import PIPE
import re
import pathlib
from tempfile import TemporaryDirectory
import json
import distutils.spawn

import yaml

from vsi.tools.diff import dict_diff
from vsi.tools.python import nested_patch

from terra import settings
from terra.core.settings import TerraJSONEncoder, filename_suffixes
from terra.compute import compute
from terra.compute.base import ServiceRunFailed
from terra.compute.container import ContainerService
from terra.compute.just import JustCompute
from terra.logger import getLogger, DEBUG1
logger = getLogger(__name__)


docker_volume_re = r'^(([a-zA-Z]:[/\\])?[^:]*):(([a-zA-Z]:[/\\])?[^:]*)' \
                   r'((:ro|:rw|:z|:Z|:r?shared|:r?slave|:r?private|' \
                   r':delegated|:cached|:consistent|:nocopy)*)$'
'''str: A regular expression to parse old style docker volume strings

RE Groups

* 0: Source
* 1: Junk - source drive (windows)
* 2: Target
* 3: Junk - target drive (windows)
* 4: Flags
* 5: Junk - last flag
'''


class Compute(JustCompute):
  '''
  Docker compute model, specifically ``docker-compose``
  '''

  def run_service(self, service_info):
    '''
    Use the service class information to run the service runner in a docker
    using

    .. code-block:: bash

        just --wrap Just-docker-compose \\
            -f {service_info.compose_file} \\
            run {service_info.compose_service_name} \\
            {service_info.command}
    '''
    pid = self.just("--wrap", "Just-docker-compose",
                    '-f', service_info.compose_file,
                    'run', service_info.compose_service_name,
                    *(service_info.command),
                    env=service_info.env)

    if pid.wait() != 0:
      raise ServiceRunFailed()

  def config_service(self, service_info, extra_compose_files=[]):
    '''
    Returns the ``docker-compose config`` output
    '''

    args = ["--wrap", "Just-docker-compose",
            '-f', service_info.compose_file] + \
        sum([['-f', extra] for extra in extra_compose_files], []) + \
        ['config']

    pid = self.just(*args, stdout=PIPE,
                    env=service_info.env)
    return pid.communicate()[0]

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

    config = yaml.load(self.config(service_info, extra_compose_files))

    if 'services' in config and \
        service_info.compose_service_name in config['services'] and \
        config['services'][service_info.compose_service_name]:
      volumes = config['services'][service_info.compose_service_name].get(
        'volumes', [])
    else:
      volumes = []

    for volume in volumes:
      if isinstance(volume, dict):
        if volume['type'] == 'bind':
          volume_map.append((volume['source'], volume['target']))
      else:
        if volume.startswith('/'):
          ans = re.match(docker_volume_re, volume).groups()
          volume_map.append((ans[0], ans[2]))

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
