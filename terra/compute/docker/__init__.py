from envcontext import EnvironmentContext
import os
from os import environ as env
from subprocess import Popen, PIPE
from shlex import quote
import re

import yaml

from vsi.tools.diff import dict_diff

from terra.compute.base import BaseService, BaseCompute
from terra.compute.utils import load_service
from terra.logger import getLogger, DEBUG1
logger = getLogger(__name__)

docker_volume_re = r'^(([a-zA-Z]:[/\\])?[^:]*):(([a-zA-Z]:[/\\])?[^:]*)((:ro|:rw|:z|:Z|:r?shared|:r?slave|:r?private|:delegated|:cached|:consistent|:nocopy)*)$'
'''str: A regular expression to parse old style docker volume strings

RE Groups

* 0: Source
* 1: Junk - source drive (windows)
* 2: Target
* 4: Junk - target drive (windows)
* 5: Flags
* 6: Junk - last flag
'''

class Compute(BaseCompute):
  '''
  Docker compute model, specifically ``docker-compose``
  '''

  docker_volume_re = r'^(([a-zA-Z]:[/\\])?[^:]*):(([a-zA-Z]:[/\\])?[^:]*)((:ro|:rw|:z|:Z|:r?shared|:r?slave|:r?private|:delegated|:cached|:consistent|:nocopy)*)$'

  def just(self, *args, **kwargs):
    '''
    Run a ``just`` command. Primarily used to run
    ``--wrap Just-docker-compose``

    Arguments
    ---------
    *args :
        List of arguments to be pass to ``just``
    **kwargs :
        Arguments sent to Popen command
    '''
    logger.debug('Running: ' + ' '.join(
        # [quote(f'{k}={v}') for k, v in env.items()] +
        [quote(x) for x in ('just',) + args]))
    env = kwargs.pop('env', {})
    env['JUSTFILE'] = os.path.join(os.environ['TERRA_TERRA_DIR'], 'Justfile')

    if logger.getEffectiveLevel() <= DEBUG1:
      dd = dict_diff(os.environ, env)[3]
      if dd:
        logger.debug1('Environment Modification:\n' + '\n'.join(dd))

    with EnvironmentContext(**env):
      pid = Popen(('just',) + args, **kwargs)
      pid.wait()
      return pid

  def run(self, service_class):
    '''
    Use the service class information to run the service runner in a docker
    using

    .. code-block:: bash

        just --wrap Just-docker-compose \\
            -f {service_info.compose_file} \\
            run {service_info.compose_service_name} \\
            {service_info.command}
    '''
    service_info = load_service(service_class)
    service_info.pre_run(self)

    self.just("--wrap", "Just-docker-compose",
              '-f', service_info.compose_file,
              'run', service_info.compose_service_name,
              *(service_info.command),
              env=service_info.env)

    service_info.post_run(self)

  def config(self, service_class):
    '''
    Returns the ``docker-compose config`` output
    '''
    service_info = load_service(service_class)
    pid = self.just("--wrap", "Just-docker-compose",
                    '-f', service_info.compose_file,
                    'config', stdout=PIPE,
                    env=service_info.env)
    return pid.communicate()[0]

  def configuration_map(self, service_class):
    '''
    Returns the mapping of volumes from the host to the container.

    Returns
    -------
    list
        Return a list of tuple pairs [(host, remote), ... ] of the volumes
        mounted from the host to container
    """

    '''
    volume_map = []

    service_info = load_service(service_class)
    config = yaml.load(self.config(service_info))

    for volume in config['services'][service_info.compose_service_name].get('volumes', []):
      if isinstance(volume, dict):
        if volume['type'] == 'bind':
          volume_map.append([volume['source'], volume['target']])
      else:
        if volume.startswith('/'):
          ans = re.match(docker_volume_re, volume).groups()
          volume_map.append([ans[0], ans[2]])

    return volume_map + service_info.volumes


class Service(BaseService):
  '''
  Base docker service class
  '''

  def __init__(self):
    super().__init__()
    self.volumes_flags = []

  def pre_run(self, compute): # Compute?
    self.temp_dir = None
    # TODO: Create temp config dir
    # TODO: Write out docker-compose.yaml containing self.volumes. Use config_dir
    volume_map = compute.configuration_map(self)

    # TODO: config -> dict
    # TODO: translate config dict:
    # TODO:   In reverse order
    # TODO:   Only tranlate once per entry
    # TODO:   Only entried ending in _path, _file, _dir
    # TODO: Write config file

  def post_run(self):
    self.temp_dir = None # TODO: Delete temp_dir

  def add_volume(self, local, remote, flags=None):
    self.volumes.append([local, remote])
    self.volumes_flags.append(flags)
