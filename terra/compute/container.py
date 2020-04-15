import os
import posixpath
import ntpath
from os import environ as env
import re
import pathlib
from tempfile import TemporaryDirectory
import json

from terra import settings
from terra.core.settings import TerraJSONEncoder
from terra.compute import compute
from terra.compute.utils import translate_settings_paths
from terra.compute.base import BaseService
from terra.logger import getLogger
logger = getLogger(__name__)


class ContainerService(BaseService):
  '''
  Base container service class
  '''

  def __init__(self):
    super().__init__()
    self.volumes_flags = []
    # For WCOW, set to 'windows'
    self.container_platform = 'linux'
    self.extra_compose_files = []

  def pre_run(self):
    # Need to run Base's pre_run first, so it has a change to update settings
    # for special exectutors, etc...
    super().pre_run()

    self.temp_dir = TemporaryDirectory()
    temp_dir = pathlib.Path(self.temp_dir.name)

    # Check to see if and are already defined, this will play nicely with
    # external influences
    env_volume_index = 1
    while f'{env["JUST_PROJECT_PREFIX"]}_VOLUME_{env_volume_index}' in \
        self.env:
      env_volume_index += 1

    # Setup volumes for container
    self.env[f'{env["JUST_PROJECT_PREFIX"]}_VOLUME_{env_volume_index}'] = \
        f'{str(temp_dir)}:/tmp_settings:rw'
    env_volume_index += 1

    # Copy self.volumes to the environment variables
    for _, ((volume_host, volume_container), volume_flags) in \
        enumerate(zip(self.volumes, self.volumes_flags)):
      volume_str = f'{volume_host}:{volume_container}'
      if volume_flags:
        volume_str += f':{volume_flags}'
      self.env[f'{env["JUST_PROJECT_PREFIX"]}_VOLUME_{env_volume_index}'] = \
          volume_str
      env_volume_index += 1

    volume_map = compute.configuration_map(self)

    logger.debug3("Compute Volume map: %s", volume_map)

    # Setup config file for container

    self.env['TERRA_SETTINGS_FILE'] = '/tmp_settings/config.json'

    container_config = translate_settings_paths(
        TerraJSONEncoder.serializableSettings(settings),
        volume_map,
        self.container_platform)

    if os.name == "nt":  # pragma: no linux cover
      # logger.warning("Windows volume mapping is experimental.")

      # Prevent the setting file name from being expanded.
      self.env['TERRA_AUTO_ESCAPE'] = self.env['TERRA_AUTO_ESCAPE'] \
          + '|TERRA_SETTINGS_FILE'

    # Dump the settings
    container_config['terra']['zone'] = 'runner'
    with open(temp_dir / 'config.json', 'w') as fid:
      json.dump(container_config, fid)

    # Dump the original setting too, incase an executor needs to perform map
    # translation too
    with open(temp_dir / 'config.json.orig', 'w') as fid:
      json.dump(TerraJSONEncoder.serializableSettings(settings), fid)

  def post_run(self):
    super().post_run()
    # Delete temp_dir
    self.temp_dir.cleanup()
    # self.temp_dir = None # Causes a warning, hopefully there wasn't a reason
    # I did it this way.

  def add_volume(self, local, remote, flags=None, prefix=None,
                 local_must_exist=False):
    '''
    Add a volume to the service
    '''

    self._validate_volume(local, remote, local_must_exist=local_must_exist)

    if self.container_platform == "windows":
      path = ntpath
    else:
      path = posixpath

    # WCOW
    if self.container_platform == "windows":
      if prefix:
        remote_drive, remote = ntpath.splitdrive(remote)
        prefix_drive, prefix = ntpath.splitdrive(prefix)
        # If prefix drive is unset, copy from remote
        if not prefix_drive:
          prefix_drive = remote_drive
        remote = ntpath.join(prefix_drive, '\\' + prefix.lstrip(r'\/'),
                             remote.lstrip(r'\/'))
    else:
      # If LCOW
      if os.name == "nt":
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
