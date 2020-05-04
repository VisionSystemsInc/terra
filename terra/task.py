import json
from os import environ as env
import os
from tempfile import gettempdir

from celery import Task, shared_task as original_shared_task

from vsi.tools.python import args_to_kwargs, ARGS, KWARGS

from terra import settings
from terra.core.settings import TerraJSONEncoder
from terra.executor import Executor
import terra.logger
import terra.compute.utils
from terra.logger import getLogger
logger = getLogger(__name__)

__all__ = ['TerraTask', 'shared_task']


def shared_task(*args, **kwargs):
  kwargs['bind'] = kwargs.pop('bind', True)
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

  def _get_volume_mappings(self):
    executor_volume_map = self.request.settings['executor']['volume_map']

    if executor_volume_map:
      compute_volume_map = \
          self.request.settings['compute']['volume_map']
      # Flip each mount point, so it goes from runner to controller
      reverse_compute_volume_map = [[x[1], x[0]]
                                    for x in compute_volume_map]
      # Revere order. This will be important in case one mount point mounts
      # inside another
      reverse_compute_volume_map.reverse()

      reverse_executor_volume_map = [[x[1], x[0]]
                                    for x in executor_volume_map]
      reverse_executor_volume_map.reverse()

    else:
      reverse_compute_volume_map = []
      compute_volume_map = []
      reverse_executor_volume_map = []

    return (compute_volume_map, reverse_compute_volume_map,
            executor_volume_map, reverse_executor_volume_map)

  def translate_paths(self, payload, reverse_compute_volume_map,
                      executor_volume_map):
    if reverse_compute_volume_map or executor_volume_map:
      # If either translation is needed, start by applying the ~ home dir
      # expansion and settings_property(which wouldn't have made it through
      # pure json conversion, but the ~ will
      payload = TerraJSONEncoder.serializableSettings(payload)
      # Go from compute runner to master controller
      if reverse_compute_volume_map:
        payload = terra.compute.utils.translate_settings_paths(
            payload, reverse_compute_volume_map)
      # Go from master controller to exector
      if executor_volume_map:
        payload = terra.compute.utils.translate_settings_paths(
            payload, executor_volume_map)
    return payload

  def apply_async(self, args=None, kwargs=None, task_id=None,
                  *args2, **kwargs2):
    current_settings = TerraJSONEncoder.serializableSettings(settings)
    return super().apply_async(args=args, kwargs=kwargs,
                               headers={'settings': current_settings},
                               task_id=task_id, *args2, **kwargs2)

  # Don't need to apply translations for apply, it runs locally
  # def apply(self, *args, **kwargs):
  #   # TerraTask._patch_settings(args, kwargs)
  #   return super().apply(*args, settings={'X': 15}, **kwargs)

  def __call__(self, *args, **kwargs):
    # this is only set when apply_async was called.
    if getattr(self.request, 'settings', None):
      if not settings.configured:
        # Cover a potential (unlikely) corner case where setting might not be
        # configured yet
        settings.configure({'processing_dir': gettempdir()})
      with settings:
        # Calculate the exector's mapped version of the runner's settings
        compute_volume_map, reverse_compute_volume_map, \
        executor_volume_map, reverse_executor_volume_map = \
            self._get_volume_mappings()

        # Load the executor version of the runner's settings
        settings._wrapped.clear()
        settings._wrapped.update(self.translate_paths(self.request.settings,
            reverse_compute_volume_map, executor_volume_map))
        # Just in case processing dir doesn't exists
        if not os.path.exists(settings.processing_dir):
          logger.critical(f'Dir "{settings.processing_dir}" is not accessible '
                          'by the executor, please make sure the worker has '
                          'access to this directory')
          settings.processing_dir = gettempdir()
          logger.warning('Using temporary directory: '
                         f'"{settings.processing_dir}" for the processing dir')

        logger.error('SGR - TerraTask ZONE ' + str(settings.terra.zone))

        settings.terra.zone = 'task' # was runner
        # Calculate the exector's mapped version of the arguments
        kwargs = args_to_kwargs(self.run, args, kwargs)
        args_only = kwargs.pop(ARGS, ())
        kwargs.update(kwargs.pop(KWARGS, ()))
        kwargs = self.translate_paths(kwargs,
            reverse_compute_volume_map, executor_volume_map)
        # Set up logger to talk to master controller
        terra.logger._logs.reconfigure_logger()
        return_value = self.run(*args_only, **kwargs)
        # REVIEW the problem is the zone changes when this gets called on scope __exit__
        terra.logger._logs.reconfigure_logger()

        # Calculate the runner mapped version of the executor's return value
        return_value = self.translate_paths(return_value,
            reverse_executor_volume_map, compute_volume_map)
    else:
      # Must call (synchronous) apply or python __call__ with no volume
      # mappings
      original_zone = settings.terra.zone
      settings.terra.zone = 'task'
      try:
        return_value = self.run(*args, **kwargs)
      finally:
        settings.terra.zone = original_zone
    self.settings = None
    return return_value

class LogErrorsTask(TerraTask):
  # from https://stackoverflow.com/a/45333231/1771778
  def on_failure(self, exc, task_id, args, kwargs, einfo):
    logger.exception('Celery task failure!!!1', exc_info=exc)
    super(LogErrorsTask, self).on_failure(exc, task_id, args, kwargs, einfo)
