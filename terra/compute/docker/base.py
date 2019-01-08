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

from envcontext import EnvironmentContext


class Compute(BaseCompute):
  ''' Using docker for the computer service model, specifically docker-compose
  '''

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

  def config(self, service_class):
    service_info = service_class()
    self.just("docker-compose",
              '-f', service_info.compose_file,
              'config',
              env=service_info.env)

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

@Compute.register
class ViewAngleRetrieval(BaseViewAngleRetrieval):
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

    self.service_name = 'dsm'