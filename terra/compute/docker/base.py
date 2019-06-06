from envcontext import EnvironmentContext
import os
from os import environ as env

from subprocess import Popen

from shlex import quote

from vsi.tools.diff import dict_diff

from terra.compute.base.base import BaseService, BaseCompute
from terra.compute.utils import load_service
from terra.logger import getLogger, DEBUG1
logger = getLogger(__name__)


class Compute(BaseCompute):
  '''
  Docker compute model, specifically ``docker-compose``
  '''

  def just(self, *args, env={}):
    '''
    Run a ``just`` command. Primarily used to run
    ``--wrap Just-docker-compose``

    Arguments
    ---------
    *args :
        List of arguments to be pass to ``just``
    '''
    logger.debug('Running: ' + ' '.join(
        # [quote(f'{k}={v}') for k, v in env.items()] +
        [quote(x) for x in ('just',) + args]))
    env['JUSTFILE'] = os.path.join(os.environ['TERRA_TERRA_DIR'], 'Justfile')
    if logger.getEffectiveLevel() <= DEBUG1:
      dd = dict_diff(os.environ, env)[3]
      if dd:
        logger.debug1('Environment Modification:\n' + '\n'.join(dd))
      with EnvironmentContext(**env):
        Popen(('just',) + args).wait()

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
    service_info = load_service(service_class)()
    service_info.pre_run()

    self.just("--wrap", "Just-docker-compose",
              '-f', service_info.compose_file,
              'run', service_info.compose_service_name,
              *(service_info.command),
              env=service_info.env)

    service_info.post_run()

  def config(self, service_class):
    '''
    Prints out the ``docker-compose config`` output
    '''
    service_info = load_service(service_class)()
    self.just("Just-docker-compose",
              '-f', service_info.compose_file,
              'config',
              env=service_info.env)


class Service(BaseService):
  '''
  Base docker service class
  '''
