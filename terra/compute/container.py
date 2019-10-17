import os
import posixpath
import ntpath
from os import environ as env
import re
import pathlib
from tempfile import TemporaryDirectory
import json

from vsi.tools.python import nested_patch

from terra import settings
from terra.core.settings import TerraJSONEncoder, filename_suffixes
from terra.compute import compute
from terra.compute.base import BaseService
from terra.logger import getLogger, DEBUG1
logger = getLogger(__name__)


class ContainerService(BaseService):
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
    while f'{env["JUST_PROJECT_PREFIX"]}_VOLUME_{env_volume_index}' in self.env:
      env_volume_index += 1

    # Setup volumes for docker
    self.env[f'{env["JUST_PROJECT_PREFIX"]}_VOLUME_{env_volume_index}'] = \
        f'{str(temp_dir)}:/tmp_settings:rw'
    env_volume_index += 1

    # Copy self.volumes to the environment variables
    for index, ((volume_host, volume_container), volume_flags) in \
        enumerate(zip(self.volumes, self.volumes_flags)):
      volume_str = f'{volume_host}:{volume_container}'
      if volume_flags:
        volume_str += f':{volume_flags}'
      self.env[f'{env["JUST_PROJECT_PREFIX"]}_VOLUME_{env_volume_index}'] = volume_str
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
        if isinstance(value, str):
          value_path = pathlib.PureWindowsPath(ntpath.normpath(value))
          for vol_from, vol_to in volume_map:
            vol_from = pathlib.PureWindowsPath(ntpath.normpath(vol_from))

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
        if isinstance(value, str):
          for vol_from, vol_to in volume_map:
            if value.startswith(vol_from):
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
