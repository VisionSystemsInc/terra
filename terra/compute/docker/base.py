from terra.compute.base.base import (
    BaseCompute, DSMService as BaseDSMService,
    ViewAngleRetrieval as BaseViewAngleRetrieval
)

import compose
import os
from os import environ as env

from subprocess import Popen

from shlex import quote

from terra.logger import getLogger
logger = getLogger(__name__)
from terra import settings

import runpy
from vsi.tools.python import ArgvContext
from envcontext import EnvironmentContext
class Compute(BaseCompute):
  ''' Using docker for the computer service model, specifically docker-compose
  '''

  # services = {'dsm': DSMService}
  # services = {}

  def __init__(self):
    # self.client = docker.from_env()
    # self.image_name = env['TERRA_DOCKER_REPO'] + ':terra_' + \
    #     os.env['TERRA_USERNAME']
    super().__init__()

  # def docker_compose(self, *args, env={}):
  #   logger.debug('Running: ' + ' '.join(
  #       [quote(f'{k}={v}') for k,v in env.items()] +
  #       [quote(x) for x in ('docker-compose',) + args]))
  #   with ArgvContext('docker-compose', *args), EnvironmentContext(**env):
  #     runpy.run_module('compose')

  def just(self, *args, env={}):
    logger.debug('Running: ' + ' '.join(
        [quote(f'{k}={v}') for k,v in env.items()] +
        [quote(x) for x in ('just',) + args]))
    with EnvironmentContext(**env):
      Popen(('just',)+args).wait()


  def run(self, service_class):
    service_info = service_class()
    service_info.pre_run()

    self.just("docker-compose",
              '-f', service_info.compose_file,
              'run', service_info.service_name,
              *(service_info.command),
              env=service_info.env)

    service_info.post_run()
  #   self.docker_compose('-f', service_info.project_dir+'/docker-compose.yml',
  #                       'run', '--rm',
  #                       '-v', os.path.abspath(settings.processing_dir) +':/dem/output',
  #                       '-v', os.path.abspath(settings.image_dir) +':/dem/img_dir',
  #                       '-v', os.path.abspath(settings.roi_kml) +':/dem/dem_roi.kml',
  #                       '-v', os.path.abspath(settings.aster_dem_dir) +':/dem/aster_dem',
  #                       '-v', os.path.abspath(os.path.join(settings.processing_dir, 'params.json')) +':/dem/config.json',
  #                        service_info.service_name,
  #                       *(service_info.command),
  #                       env=service_info.env)

  def config(self, service_class):
    service_info = service_class()
    self.just("docker-compose",
              '-f', service_info.compose_file,
              'config',
              env=service_info.env)

  #   # dispatch(['config'], service_info.project_dir, service_info.environment)()
  #   dispatch(['--file', service_info.project_dir+'/docker-compose.yml', 'config'])()


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

@Compute.register
class DSMService(BaseDSMService):

  def __init__(self):
    self.command = ['python', '-m', 'source.tasks.generate_dsm']
    self.env = {
      'DSM_SOURCE_DIR': os.path.join(env['TERRA_SOURCE_DIR'], 'external',
                                      'dsm_desktop'),
      'DSM_SOURCE_DIR_DOCKER':'/vsi/source',
      'DSM_VXL_SOURCE_DIR_DOCKER': '/vxl',
      'DSM_J2K_SOURCE_DIR_DOCKER': '/vxl/v3p/j2k',
      'DSM_BUILD_DIR_DOCKER': '/vsi/build',
      'DSM_VXL_BUILD_DIR_DOCKER': '/vsi/build/vxl-build',
      'DSM_DOCKER_RUNTIME': env['TERRA_DOCKER_RUNTIME']
    }

    self.env['DSM_VXL_SOURCE_DIR'] = \
        os.path.join(self.env['DSM_SOURCE_DIR'], 'external', 'vxl')
    self.env['DSM_J2K_SOURCE_DIR'] = \
        os.path.join(self.env['DSM_SOURCE_DIR'], 'external', 'j2k_linux')
    self.env['DSM_BUILD_DIR'] = \
        os.path.join(self.env['DSM_SOURCE_DIR'], 'build-debian8')
    self.env['DSM_VXL_BUILD_DIR'] = \
        os.path.join(self.env['DSM_BUILD_DIR'], 'vxl-build')

    self.compose_file = os.path.join(env['TERRA_SOURCE_DIR'],
                                    'external', 'dsm_desktop',
                                    'docker-compose.yml')

    self.env['TERRA_DSM_VOLUME_1'] = os.path.abspath(settings.processing_dir) \
        + ':/dem/output'
    self.env['TERRA_DSM_VOLUME_2'] = os.path.abspath(settings.image_dir) \
        + ':/dem/img_dir'
    self.env['TERRA_DSM_VOLUME_3'] = os.path.abspath(settings.roi_kml) \
        + ':/dem/dem_roi.kml'
    self.env['TERRA_DSM_VOLUME_4'] = os.path.abspath(settings.aster_dem_dir) \
        + ':/dem/aster_dem'

    self.param_file = os.path.abspath(os.path.join(settings.processing_dir,
                                                   'params.json'))
    self.env['TERRA_DSM_VOLUME_5'] = self.param_file+':/dem/config.json'


    self.service_name = 'dsm'

  def pre_run(self):
    import json
    with open(self.param_file, 'w') as fid:
      json.dump(settings.params, fid)


class ViewAngleRetrieval(BaseViewAngleRetrieval):
  def __init__(self):
    self.command = ['python', '-m', 'source.tasks.generate_dsm']
    # compose_file = os.path.join(env['TERRA_SOURCE_DIR'], 'external', 'dsm_desktop', 'docker-compose.yml')
    self.env = {
      'DSM_SOURCE_DIR': os.path.join(env['TERRA_SOURCE_DIR'], 'external',
                                      'dsm_desktop'),
      'DSM_SOURCE_DIR_DOCKER':'/vsi/source',
      'DSM_VXL_SOURCE_DIR_DOCKER': '/vxl',
      'DSM_J2K_SOURCE_DIR_DOCKER': '/vxl/v3p/j2k',
      'DSM_BUILD_DIR_DOCKER': '/vsi/build',
      'DSM_VXL_BUILD_DIR_DOCKER': '/vsi/build/vxl-build',
      'DSM_DOCKER_RUNTIME': env['TERRA_DOCKER_RUNTIME']
    }

    self.env['DSM_VXL_SOURCE_DIR'] = \
        os.path.join(self.env['DSM_SOURCE_DIR'], 'external', 'vxl')
    self.env['DSM_J2K_SOURCE_DIR'] = \
        os.path.join(self.env['DSM_SOURCE_DIR'], 'external', 'j2k_linux')
    self.env['DSM_BUILD_DIR'] = \
        os.path.join(self.env['DSM_SOURCE_DIR'], 'build-debian8')
    self.env['DSM_VXL_BUILD_DIR'] = \
        os.path.join(self.env['DSM_BUILD_DIR'], 'vxl-build')

    self.compose_file = os.path.join(env['TERRA_SOURCE_DIR'],
                                    'external', 'dsm_desktop',
                                    'docker-compose.yml')

    self.service_name = 'dsm'