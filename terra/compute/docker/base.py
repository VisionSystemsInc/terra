from terra.compute.base.base import BaseCompute

import compose
import os
from os import environ as env

from compose.config.environment import Environment
from compose.cli.command import set_parallel_limit, get_project, get_config_path_from_options
from compose.cli.main import build_container_options, run_one_off_container
from compose.cli.errors import UserError
from compose.cli.docker_client import tls_config_from_options

def project_from_options(project_dir, options, environment={}):
  ''' Version of ``compose.cli.project_from_options`` with environment vars
  '''
  environment = Environment.from_env_file(project_dir)
  environment.update(env)
  set_parallel_limit(environment)

  host = options.get('--host')
  if host is not None:
    host = host.lstrip('=')
  return get_project(
    project_dir,
    get_config_path_from_options(project_dir, options, environment),
    project_name=options.get('--project-name'),
    verbose=options.get('--verbose'),
    host=host,
    tls_config=tls_config_from_options(options, environment),
    environment=environment,
    override_dir=options.get('--project-directory'),
    compatibility=options.get('--compatibility'),
  )

class DSMService(BaseCompute.DSMService):
  def __init__(self):
    self.service_name = "dsm"
    self.command = ['python', '-m', 'source.tasks.generate_dsm']
    # compose_file = os.path.join(env['TERRA_SOURCE_DIR'], 'external', 'dsm_desktop', 'docker-compose.yml')
    environment = {
      'DSM_SOURCE_DIR': os.path.join(env['TERRA_SOURCE_DIR'], 'external',
                                      'dsm_desktop'),
      'DSM_SOURCE_DIR_DOCKER':'/vsi/source',
      'DSM_VXL_SOURCE_DIR_DOCKER': '/vxl',
      'DSM_J2K_SOURCE_DIR_DOCKER': '/vxl/v3p/j2k',
      'DSM_BUILD_DIR_DOCKER': '/vsi/build',
      'DSM_VXL_BUILD_DIR_DOCKER': '/vsi/build/vxl-build',
      'DSM_DOCKER_RUNTIME': env['TERRA_DOCKER_RUNTIME']
    }

    environment['DSM_VXL_SOURCE_DIR'] = \
        os.path.join(environment['DSM_SOURCE_DIR'], 'external', 'vxl')
    environment['DSM_J2K_SOURCE_DIR'] = \
        os.path.join(environment['DSM_SOURCE_DIR'], 'external', 'j2k_linux')
    environment['DSM_BUILD_DIR'] = \
        os.path.join(environment['DSM_SOURCE_DIR'], 'build-debian8')
    environment['DSM_VXL_BUILD_DIR'] = \
        os.path.join(environment['DSM_BUILD_DIR'], 'vxl-build')

    self.project_dir = os.path.join(env['TERRA_SOURCE_DIR'],
                                    'external', 'dsm_desktop')
    # self.project = project_from_options(self.project_dir, {}, environment)
    # self.environment = environment
    env.update(environment)

from compose.cli.docopt_command import DocoptDispatcher
from compose.cli.main import TopLevelCommand, perform_command
from compose.cli.utils import get_version_info
# import compose.cli.errors as errors
import functools

def dispatch(args):
  # setup_logging()
  dispatcher = DocoptDispatcher(
    TopLevelCommand,
    {'options_first': True, 'version': get_version_info('compose')})

  options, handler, command_options = dispatcher.parse(args)
  # setup_console_handler(console_handler,
  #                       options.get('--verbose'),
  #                       options.get('--no-ansi'),
  #                       options.get("--log-level"))
  # setup_parallel_logger(options.get('--no-ansi'))
  if options.get('--no-ansi'):
    command_options['--no-color'] = True
  return functools.partial(perform_command, options, handler, command_options)

# def perform_command(options, handler, command_options, project_dir='.', environment={}):
#     if options['COMMAND'] in ('help', 'version'):
#         # Skip looking up the compose file.
#         handler(command_options)
#         return

#     if options['COMMAND'] == 'config':
#         command = TopLevelCommand(None, options=options)
#         handler(command, command_options)
#         return

#     print(environment)
#     project = project_from_options(project_dir, options, environment)
#     command = TopLevelCommand(project, options=options)
#     with errors.handle_connection_errors(project.client):
#         handler(command, command_options)


class Compute(BaseCompute):
  ''' Using docker for the computer service model, specifically docker-compose
  '''

  services = {'dsm': DSMService}

  def __init__(self):
    # self.client = docker.from_env()
    # self.image_name = env['TERRA_DOCKER_REPO'] + ':terra_' + \
    #     os.env['TERRA_USERNAME']
    super().__init__()

  def run(self, service_class, options={}):
    service_info = service_class()

    dispatch(['--file', service_info.project_dir+'/docker-compose.yml', 'run', service_info.service_name] + service_info.command)()

  def config(self, service_class, options={}):
    service_info = service_class()

    # dispatch(['config'], service_info.project_dir, service_info.environment)()
    dispatch(['--file', service_info.project_dir+'/docker-compose.yml', 'config'])()


    # options['SERVICE'] = service_info.service_name
    # if hasattr(service_info, 'command'):
    #   options['COMMAND'] = service_info.command

    # service = service_info.project.get_service(options['SERVICE'])
    # detach = options.get('--detach')

    # if options.get('--publish', None) and options.get('--service-ports', None):
    #     raise UserError(
    #         'Service port mapping and manual port mapping '
    #         'can not be used together'
    #     )

    # if options['COMMAND'] is not None:
    #     command = [options['COMMAND']] + options.get('ARGS', [])
    # elif options.get('--entrypoint', None) is not None:
    #     command = []
    # else:
    #     command = service.options.get('command')

    # container_options = build_container_options(options, detach, command)
    # run_one_off_container(
    #     container_options, service_info.project, service, options,
    #     {}, service_info.project_dir
    # )