import os
from tempfile import gettempdir

from celery import shared_task as original_shared_task
from celery.app.task import Task

from vsi.tools.python import args_to_kwargs, ARGS, KWARGS

from terra import settings
from terra.core.settings import TerraJSONEncoder
import terra.logger
import terra.compute.utils
from terra.logger import getLogger
logger = getLogger(__name__)

__all__ = ['TerraTask', 'shared_task']


# Take the shared task decorator, and add some Terra defaults, so you don't
# need to specify them EVERY task
def shared_task(*args, **kwargs):
  kwargs['bind'] = kwargs.pop('bind', True)
  kwargs['base'] = kwargs.pop('base', TerraTask)
  return original_shared_task(*args, **kwargs)


class TerraTask(Task):
  def _get_volume_mappings(self):
    executor_volume_map = self.request.settings['executor']['volume_map']

    if executor_volume_map:
      compute_volume_map = \
          self.request.settings['compute']['volume_map']
      # Flip each mount point, so it goes from runner to controller
      reverse_compute_volume_map = [[x[1], x[0]]
                                    for x in compute_volume_map]
      # Reverse order. This will be important in case one mount point mounts
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
      # expansion and settings_property (which wouldn't have made it through
      # pure json conversion, but the ~ will)
      payload = TerraJSONEncoder.serializableSettings(payload)
      # Go from compute runner to master controller
      if reverse_compute_volume_map:
        payload = terra.compute.utils.translate_settings_paths(
            payload, reverse_compute_volume_map)
      # Go from master controller to executor
      if executor_volume_map:
        payload = terra.compute.utils.translate_settings_paths(
            payload, executor_volume_map)
    return payload

  # Don't need to apply translations for apply, it runs locally
  # def apply(self, *args, **kwargs):

  # apply_async needs to smuggle a copy of the settings to the task
  def apply_async(self, args=None, kwargs=None, task_id=None,
                  *args2, **kwargs2):
    current_settings = TerraJSONEncoder.serializableSettings(settings)
    return super().apply_async(args=args, kwargs=kwargs,
                               headers={'settings': current_settings},
                               task_id=task_id, *args2, **kwargs2)

  def __call__(self, *args, **kwargs):
    # this is only set when apply_async was called.
    logger.debug4(f"Running task: {self} with args {args} and kwargs {kwargs}")
    if getattr(self.request, 'settings', None):
      if not settings.configured:
        # Cover a potential (unlikely) corner case where setting might not be
        # configured yet
        settings.configure({'processing_dir': gettempdir()})

      # Create a settings context, so I can replace it with the task's settings
      with settings:
        # Calculate the exector's mapped version of the runner's settings
        compute_volume_map, reverse_compute_volume_map, \
            executor_volume_map, reverse_executor_volume_map = \
            self._get_volume_mappings()

        # Load the executor version of the runner's settings
        settings._wrapped.clear()
        settings._wrapped.update(self.translate_paths(
            self.request.settings,
            reverse_compute_volume_map,
            executor_volume_map))
        # This is needed here because I just loaded settings from a runner!
        settings.terra.zone = 'task'

        # Just in case processing dir doesn't exist
        if not os.path.exists(settings.processing_dir):
          logger.critical(f'Dir "{settings.processing_dir}" is not accessible '
                          'by the executor, please make sure the worker has '
                          'access to this directory')
          settings.processing_dir = gettempdir()
          logger.warning('Using temporary directory: '
                         f'"{settings.processing_dir}" for the processing dir')

        # Calculate the executor's mapped version of the arguments
        kwargs = args_to_kwargs(self.run, args, kwargs)
        args_only = kwargs.pop(ARGS, ())
        kwargs.update(kwargs.pop(KWARGS, ()))
        kwargs = self.translate_paths(kwargs,
                                      reverse_compute_volume_map,
                                      executor_volume_map)
        # Set up logger to talk to master controller
        terra.logger._logs.reconfigure_logger(pre_run_task=True)
        return_value = self.run(*args_only, **kwargs)

        # Calculate the runner mapped version of the executor's return value
        return_value = self.translate_paths(return_value,
                                            reverse_executor_volume_map,
                                            compute_volume_map)
    else:
      # Must call (synchronous) apply or python __call__ with no volume
      # mappings
      # Use a flag for people who are somehow getting here with settings
      # unconfigured
      original_zone = None
      if settings.configured:
        original_zone = settings.terra.zone
      settings.terra.zone = 'task'
      try:
        return_value = self.run(*args, **kwargs)
      finally:
        if original_zone is not None:
          settings.terra.zone = original_zone
    return return_value

  # # from https://stackoverflow.com/a/45333231/1771778
  # def on_failure(self, exc, task_id, args, kwargs, einfo):
  #   logger.exception('Celery task failure!!!', exc_info=exc)
  #   return super().on_failure(exc, task_id, args, kwargs, einfo)
