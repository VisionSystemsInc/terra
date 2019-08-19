import os
import posixpath
import ntpath
from os import environ as env
from subprocess import Popen, PIPE
from shlex import quote
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
from terra.compute.base import BaseService, BaseCompute, ServiceRunFailed
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


class Compute(BaseCompute):
  '''
  Docker compute model, specifically ``docker-compose``
  '''

  def just(self, *args, **kwargs):
    '''
    Run a ``just`` command. Primarily used to run
    ``--wrap Just-docker-compose``

    Arguments
    ---------
    justfile : :class:`str`, optional
        Optionally allow you to specify a custom ``Justfile``. Defaults to
        Terra's ``Justfile`` is used, which is the correct course of action
        most of the time
    env : :class:`dict`, optional
        Sets environment variables. Same as Popen's ``env``, except
        ``JUSTFILE`` is programatically set, and cannot be overridden any other
        way than chaning the ``justfile`` variable
    *args :
        List of arguments to be pass to ``just``
    **kwargs :
        Arguments sent to ``Popen`` command
    '''

    logger.debug('Running: ' + ' '.join(
        [quote(x) for x in ('just',) + args]))

    just_env = kwargs.pop('env', env).copy()
    justfile = kwargs.pop(
        'justfile', os.path.join(env['TERRA_TERRA_DIR'], 'Justfile'))
    just_env['JUSTFILE'] = justfile

    if logger.getEffectiveLevel() <= DEBUG1:
      dd = dict_diff(env, just_env)[3]
      if dd:
        logger.debug1('Environment Modification:\n' + '\n'.join(dd))

    # Get bash path for windows compatibility. I can't explain this error, but
    # while the PATH is set right, I can't call "bash" because the WSL bash is
    # called instead. It appears to be a bug in the windows kernel as
    # subprocess._winapi.CreateProcess('bash', 'bash --version', None, None,
    # 0, 0, os.environ, None, None) even fails.
    # Microsoft probably has a special exception for the word "bash" that
    # calls WSL bash on execute :(
    kwargs['executable'] = distutils.spawn.find_executable('bash')
    # Have to call bash for windows compatibility, no shebang support
    pid = Popen(('bash', 'just') + args, env=just_env, **kwargs)
    return pid

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


class Service(BaseService):
  '''
  Base docker service class
  '''

  def __init__(self):
    super().__init__()
    self.volumes_flags = []
    # For WCOW, set to 'windows'
    self.container_platform = 'linux'

  def pre_run(self):
    self.temp_dir = TemporaryDirectory()
    temp_dir = pathlib.Path(self.temp_dir.name)

    # Check to see if and are already defined, this will play nicely with
    # external influences
    env_volume_index = 1
    while f'TERRA_VOLUME_{env_volume_index}' in self.env:
      env_volume_index += 1

    # Setup volumes for docker
    self.env[f'TERRA_VOLUME_{env_volume_index}'] = \
        f'{str(temp_dir)}:/tmp_settings:rw'
    env_volume_index += 1

    # Copy self.volumes to the environment variables
    for index, ((volume_host, volume_container), volume_flags) in \
        enumerate(zip(self.volumes, self.volumes_flags)):
      volume_str = f'{volume_host}:{volume_container}'
      if volume_flags:
        volume_str += f':{volume_flags}'
      self.env[f'TERRA_VOLUME_{env_volume_index}'] = volume_str
      env_volume_index += 1

    # volume_map = compute.configuration_map(self, [str(temp_compose_file)])
    volume_map = compute.configuration_map(self)

    logger.debug3("Volume map: %s", volume_map)

    # Setup config file for docker
    docker_config = TerraJSONEncoder.serializableSettings(settings)

    self.env['TERRA_SETTINGS_FILE'] = '/tmp_settings/config.json'

    if os.name == "nt":
      logger.warning("Windows volume mapping is experimental.")

      # Prevent the setting file name from being expanded.
      self.env['TERRA_AUTO_ESCAPE'] = self.env['TERRA_AUTO_ESCAPE'] \
                                      + '|TERRA_SETTINGS_FILE'

      def patch_volume(value, volume_map):
        value_path = pathlib.PureWindowsPath(ntpath.normpath(value))
        for vol_from, vol_to in volume_map:
          vol_from = pathlib.PureWindowsPath(ntpath.normpath(vol_from))

          if isinstance(value, str):
            try:
              remainder = value_path.relative_to(vol_from)
            except ValueError:
              continue
            if self.container_platform == "windows":
              value = pathlib.PureWindowsPath(vol_to)
            else:
              value = pathlib.PurePosixPath(vol_to)

            value /= remainder
            return str(value)
        return value
    else:
      def patch_volume(value, volume_map):
        for vol_from, vol_to in volume_map:
          if isinstance(value, str) and value.startswith(vol_from):
            return value.replace(vol_from, vol_to, 1)
        return value

    # Apply map translation to settings configuration
    docker_config = nested_patch(
        docker_config,
        lambda key, value: (isinstance(key, str)
                            and any(key.endswith(pattern)
                                    for pattern in filename_suffixes)),
        lambda key, value: patch_volume(value, reversed(volume_map))
    )

    # Dump the settings
    with open(temp_dir / 'config.json', 'w') as fid:
      json.dump(docker_config, fid)

  def post_run(self):
    # Delete temp_dir
    self.temp_dir.cleanup()
    # self.temp_dir = None # Causes a warning, hopefully there wasn't a reason
    # I did it this way.

  def add_volume(self, local, remote, flags=None, prefix=None):
    if self.container_platform == "windows":
      path = ntpath
    else:
      path = posixpath

    # If LCOW
    if os.name == "nt" and self.container_platform == "linux":
      # Convert to posix slashed
      remote = remote.replace('\\', '/')
      # Remove duplicates
      remote = re.sub('//+', '/', remote)
      # Split drive letter off
      drive, remote = ntpath.splitdrive(remote)
      if drive:
        remote = posixpath.join('/', drive[0], remote.lstrip(r'\/'))

    if prefix:
      remote = path.join(prefix, remote.lstrip(r'\/'))

    self.volumes.append((local, remote))
    self.volumes_flags.append(flags)
