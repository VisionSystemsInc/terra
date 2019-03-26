from envcontext import EnvironmentContext
import os
from os import environ as env

from subprocess import Popen

from shlex import quote

from terra.compute.base.base import BaseCompute
# from terra import settings
from terra.compute.utils import load_service
from terra.logger import getLogger
logger = getLogger(__name__)


class Compute(BaseCompute):
  ''' Using docker for the computer service model, specifically docker-compose
  '''

  def just(self, *args, env={}):
    logger.debug('Running: ' + ' '.join(
        [quote(f'{k}={v}') for k, v in env.items()] +
        [quote(x) for x in ('just',) + args]))
    with EnvironmentContext(**env):
      Popen(('just',) + args).wait()

  def run(self, service_class):
    service_info = load_service(service_class)()
    service_info.pre_run()

    self.just("docker-compose",
              '-f', service_info.compose_file,
              'run', service_info.compose_service_name,
              *(service_info.command),
              env=service_info.env)

    service_info.post_run()

  def config(self, service_class):
    service_info = load_service(service_class)()
    self.just("docker-compose",
              '-f', service_info.compose_file,
              'config',
              env=service_info.env)


class DockerService:
  pass
