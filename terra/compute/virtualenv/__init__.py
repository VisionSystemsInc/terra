import os
import subprocess

from envcontext import EnvironmentContext

from terra.compute.base import BaseService, BaseCompute, ServiceRunFailed
from terra.compute.utils import load_service
from terra.logger import getLogger
from terra import settings
logger = getLogger(__name__)


class Compute(BaseCompute):
  '''
  Virtual env computing model
  '''

  # run the service in a virtual env with the subprocess module
  def run(self, service_class):
    service_info = load_service(service_class)

    # pre run
    logger.debug2("pre-running %s ", str(service_info))
    service_info.pre_run()

    # Replace 'python' command with virtual environment python executable
    if settings.compute.get('virtualenv_dir', None):
      service_info.env['PATH'] = settings.compute.virtualenv_dir \
        + os.path.pathsep + service_info.env['PATH']
      # TODO: Not sure if I want this or not
      # if "_OLD_VIRTUAL_PATH" in service_info.env:
      #   service_info.env['PATH'] = service_info.env["_OLD_VIRTUAL_PATH"]
      # service_info.command = [settings.compute.venv_python
      #                         if el == 'python' else el
      #                         for el in service_info.command]

    # run command -- command must be a list of strings
    with EnvironmentContext(service_info.env):
      pid = subprocess.Popen(service_info.command, env=service_info.env)

    if pid.wait() != 0:
      raise(ServiceRunFailed())

    # post run
    logger.debug2("post-running %s ", str(service_info))
    service_info.post_run()


class Service(BaseService):
  '''
  Base service class, prints pre_run and post_run steps
  '''
