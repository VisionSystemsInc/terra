import json
from os import environ as env
import os
from tempfile import gettempdir

from celery import Task, shared_task as original_shared_task

from terra import settings
from terra.core.settings import TerraJSONEncoder
from terra.executor import Executor
import terra.logger
import terra.compute.utils
from terra.logger import getLogger
logger = getLogger(__name__)

__all__ = ['TerraTask', 'shared_task']


def shared_task(*args, **kwargs):
  kwargs['bind'] = kwargs.pop('bin', True)
  kwargs['base'] = kwargs.pop('base', TerraTask)
  return original_shared_task(*args, **kwargs)


class TerraTask(Task):
  settings = None
  # @staticmethod
  # def _patch_settings(args, kwargs):
  #   if 'TERRA_EXECUTOR_SETTINGS_FILE' in env:
  #     # TODO: Cache loads for efficiency?
  #     settings = json.load(env['TERRA_EXECUTOR_SETTINGS_FILE'])

  #     # If args is not empty, the first arg was settings
  #     if args:
  #       args[0] = settings
  #     else:
  #       kwargs['settings'] = settings

  def serialize_settings(self):
    # If there is a non-empty mapping, then create a custom executor settings
    executor_volume_map = self.request.settings.pop('executor_volume_map',
                                                    None)
    if executor_volume_map:
      return terra.compute.utils.translate_settings_paths(
          TerraJSONEncoder.serializableSettings(self.request.settings),
          executor_volume_map)
    return self.request.settings

  def apply_async(self, args=None, kwargs=None, task_id=None, user=None,
                  *args2, **kwargs2):
    with open(f'{env["TERRA_SETTINGS_FILE"]}.orig', 'r') as fid:
      original_settings = json.load(fid)
    return super().apply_async(args=args, kwargs=kwargs,
                               task_id=task_id, *args2, headers={'settings': original_settings},
                               **kwargs2)

  # def apply(self, *args, **kwargs):
  #   # TerraTask._patch_settings(args, kwargs)
  #   return super().apply(*args, settings={'X': 15}, **kwargs)

  def __call__(self, *args, **kwargs):
    if getattr(self.request, 'settings', None):
      if not settings.configured:
        settings.configure({'processing_dir': gettempdir()})
      with settings:
        logger.critical(settings)
        settings._wrapped.clear()
        settings._wrapped.update(self.serialize_settings())
        if not os.path.exists(settings.processing_dir):
          logger.critical(f'Dir "{settings.processing_dir}" is not accessible '
                          'by the executor, please make sure the worker has '
                          'access to this directory')
          settings.processing_dir = gettempdir()
          logger.warning('Using temporary directory: '
                         f'"{settings.processing_dir}" for the processing dir')
        logger.critical(settings)
        settings.terra.zone = 'task'
        terra.logger._logs.reconfigure_logger()
        return_value = self.run(*args, **kwargs)
    else:
      original_zone = settings.terra.zone
      settings.terra.zone = 'task'
      return_value = self.run(*args, **kwargs)
      settings.terra.zone = original_zone
    self.settings = None
    return return_value