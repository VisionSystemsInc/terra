import distutils.spawn
import json
import os
from shlex import quote
from subprocess import Popen
from tempfile import TemporaryDirectory

from vsi.tools.diff import dict_diff
from vsi.tools.dir_util import is_subdir

from terra.compute.base import BaseService, BaseCompute, ServiceRunFailed
from terra.core.settings import TerraJSONEncoder
from terra import settings
from terra.logger import getLogger, DEBUG1
logger = getLogger(__name__)


class Compute(BaseCompute):
  '''
  Virtual env computing model
  '''

  # run the service in a virtual env with the subprocess module
  def run_service(self, service_info):
    '''
    Run a command, usually in a virtual env.

    If ``settings.compute.virtualenv_dir`` is set, then that directory is
    automatically prepended to the ``PATH`` for the command to be executed.

    Arguments
    ---------
    env : :class:`dict`, optional
        Sets environment variables. Same as Popen's ``env``, except
        ``JUSTFILE`` is programatically set, and cannot be overridden any other
        way than chaning the ``justfile`` variable
    *args :
        List of arguments to be pass to ``Popen``
    **kwargs :
        Arguments sent to ``Popen`` command
    '''

    logger.debug('Running: ' + ' '.join(
        [quote(x) for x in service_info.command]))

    env = service_info.env

    # Replace 'python' command with virtual environment python executable
    if settings.compute.virtualenv_dir:
      env['PATH'] = settings.compute.virtualenv_dir \
        + os.path.pathsep + service_info.env['PATH']
      # TODO: Not sure if I want this or not
      # if "_OLD_VIRTUAL_PATH" in service_info.env:
      #   service_info.env['PATH'] = service_info.env["_OLD_VIRTUAL_PATH"]

    if logger.getEffectiveLevel() <= DEBUG1:
      dd = dict_diff(os.environ, env)[3]
      if dd:
        logger.debug4('Environment Modification:\n' + '\n'.join(dd))

    # Similar (but different) to a bug in docker compute, the right python
    # executable is not found on the path, possibly because Popen doesn't
    # search the env's path, but this will manually search and find the right
    # command
    executable = distutils.spawn.find_executable(service_info.command[0],
                                                 path=env['PATH'])

    # Check if the executable was found in the virtualenv_dir.
    # If it wasn't, warn the user in case they made a mistake
    if settings.compute.virtualenv_dir is not None and \
       not is_subdir(executable, settings.compute.virtualenv_dir)[0]:
      logger.warning(f"Couldn't find command {service_info.command[0]} in "
                     f"virtualenv_dir {settings.compute.virtualenv_dir}. "
                     f"Using {executable} instead. If you meant to bypass the "
                     "virtualenv dir, then feel free to ignore this message. "
                     "If you weren't expecting this, then make sure the "
                     "compute.virtualenv_dir is correct.")

    # run command -- command must be a list of strings
    pid = Popen(service_info.command, env=env, executable=executable)

    if pid.wait() != 0:
      raise ServiceRunFailed(pid.returncode)

  def add_volume(self, local, no_remote=None, flags=None, prefix=None,
                 local_must_exist=False):
    '''
    Add a volume to the service
    '''

    self._validate_volume(local, None, check_remote=False,
                          local_must_exist=local_must_exist)
    self.volumes.append(local)


class Service(BaseService):
  '''
  Virtualenv service class
  '''

  def pre_run(self):
    super().pre_run()

    # Create a temp directory, store it in this instance
    self.temp_dir = TemporaryDirectory(suffix=f"_{type(self).__name__}")
    if self.env.get('TERRA_KEEP_TEMP_DIR', None) == "1":
      self.temp_dir._finalizer.detach()

    # Use a config.json file to store settings within that temp directory
    temp_config_file = os.path.join(self.temp_dir.name, 'config.json')

    # Serialize config file
    venv_config = TerraJSONEncoder.serializableSettings(settings)

    # Dump the serialized config to the temp config file
    venv_config['terra']['zone'] = 'runner'
    with open(temp_config_file, 'w') as fid:
      json.dump(venv_config, fid)

    # Set the Terra settings file for this service runner to the temp config
    # file
    self.env['TERRA_SETTINGS_FILE'] = temp_config_file

  def post_run(self):
    super().post_run()
    # Delete temp_dir
    if self.env.get('TERRA_KEEP_TEMP_DIR', None) != "1":
      # Calling this just prevents the annoying warning from saying "Hey, you
      # know that automatic cleanup? It happened! Maybe you should manually
      # call  the automatic cleanup, cause yeah, that makes sense!"
      self.temp_dir.cleanup()
