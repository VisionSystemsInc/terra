import os
import posixpath
import ntpath
import re
import pathlib
from tempfile import TemporaryDirectory
import json

from terra import settings
from terra.core.settings import TerraJSONEncoder
from terra.compute import compute
from terra.utils.path import translate_settings_paths
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

    # default compose_service_name
    app_prefixes = self._env_array('TERRA_APP_PREFIXES_AST')
    env_key = f"{app_prefixes[0]}_COMPOSE_SERVICE_RUNNER"
    self.compose_service_name = self.env.get(env_key)

  def pre_run(self):
    # Need to run Base's pre_run first, so it has a chance to update settings
    # for special executors, etc...
    super().pre_run()

    self.temp_dir = TemporaryDirectory(suffix=f"_{type(self).__name__}")
    if self.env.get('TERRA_KEEP_TEMP_DIR', None) == "1":
      self.temp_dir._finalizer.detach()
    temp_dir = pathlib.Path(self.temp_dir.name)

    # Check to see if and are already defined, this will play nicely with
    # external influences
    env_volume_index = 1
    while f'{self.env["JUST_PROJECT_PREFIX"]}_VOLUME_{env_volume_index}' in \
        self.env:
      env_volume_index += 1

    # Setup volumes for container
    self.env[f'{self.env["JUST_PROJECT_PREFIX"]}_'
             f'VOLUME_{env_volume_index}'] = \
        f'{str(temp_dir)}:/tmp_settings'
    env_volume_index += 1

    # This directory is used for both locking and setting dump, so don't
    # if settings.terra.disable_settings_dump here
    os.makedirs(settings.settings_dir, exist_ok=True)
    self.env[f'{self.env["JUST_PROJECT_PREFIX"]}_'
             f'VOLUME_{env_volume_index}'] = \
        f'{settings.settings_dir}:{self.env["TERRA_SETTINGS_DOCKER_DIR"]}'
    env_volume_index += 1

    # Always mount in the lock dir, in case the resource manager is use
    # If terra ends up needing other things mounted in, lock_dir should be
    # renamed to something more generic like terra_var_dir, and everything
    # share that, if it makes sense.
    os.makedirs(settings.terra.lock_dir, exist_ok=True)
    self.add_volume(settings.terra.lock_dir, '/var/lib/terra/lock')

    # Copy self.volumes to the environment variables
    for _, ((volume_host, volume_container), volume_flags) in \
        enumerate(zip(self.volumes, self.volumes_flags)):
      volume_str = f'{volume_host}:{volume_container}'
      if volume_flags:
        volume_str += f':{volume_flags}'
      self.env[f'{self.env["JUST_PROJECT_PREFIX"]}_'
               f'VOLUME_{env_volume_index}'] = \
          volume_str
      env_volume_index += 1

    settings.compute.volume_map = compute.configuration_map(self)
    logger.debug4("Compute Volume map: %s", settings.compute.volume_map)

    # Setup config file for container

    self.env['TERRA_SETTINGS_FILE'] = '/tmp_settings/config.json'

    container_config = translate_settings_paths(
        TerraJSONEncoder.serializableSettings(settings),
        settings.compute.volume_map,
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

  def post_run(self):
    super().post_run()
    # Delete temp_dir
    if self.env.get('TERRA_KEEP_TEMP_DIR', None) != "1":
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

  def add_volume_input(self, local, remote):
    '''
    Add a read-only input volume, confirming if the local file/folder
    exists. Raise a :obj:`ValueError` should validation fail.
    '''

    self.add_volume(local, remote, flags='ro',
                    local_must_exist=True)

  def add_file_input(self, local, remote, use_local_extension=False):
    '''
    Add a read-only input file, confirming that the local file exists.
    Maintain local file extension if requested.
    '''

    # replace remote extension with local extension
    if use_local_extension:
      local_ext = os.path.splitext(local)[1].lower()
      remote = os.path.splitext(remote)[0] + local_ext

    # update volume
    self.add_volume_input(local, remote, local_must_exist=True)

  def add_file(self, local, remote, use_local_extension=False):
    '''
    Add a input file, creating the local file if it does not exist.
    Maintain local file extension if requested.
    '''

    # replace remote extension with local extension
    if use_local_extension:
      local_ext = os.path.splitext(local)[1].lower()
      remote = os.path.splitext(remote)[0] + local_ext

    # Make sure parent exists, and is not a file
    parent = os.path.dirname(local)
    if os.path.exists(parent) and not os.path.isdir(parent):
      raise FileExitsError(  # noqa: F821
        f"{parent} exists as a file, instead of a directory")

    # update volume
    self.add_volume(local, remote)
