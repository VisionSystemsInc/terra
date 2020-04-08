from os import environ as env
from tempfile import gettempdir

from celery import Task, shared_task as original_shared_task

from terra import settings
from terra.core.settings import TerraJSONEncoder
from terra.executor import Executor
import terra.logger
import terra.compute.utils

__all__ = ['TerraTask', 'shared_task']

def shared_task(*args, **kwargs):
  kwargs['bind'] = True
  kwargs['base'] = TerraTask
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
    return super().apply_async(args=args, kwargs=kwargs,
                               task_id=task_id, *args2, headers={'settings': TerraJSONEncoder.serializableSettings(settings)},
                               **kwargs2)

  # def apply(self, *args, **kwargs):
  #   # TerraTask._patch_settings(args, kwargs)
  #   return super().apply(*args, settings={'X': 15}, **kwargs)

  def __call__(self, *args, **kwargs):
    print('111')
    if getattr(self.request, 'settings', None):
      print('222')
      if not settings.configured:
        print('333')
        settings.configure({'processing_dir': gettempdir()})
      with settings:
        print('444')
        print(settings)
        settings._wrapped.clear()
        settings._wrapped.update(self.serialize_settings())
        print(settings)
        settings.processing_dir=gettempdir()
        terra.logger._logs.reconfigure_logger()
        return_value = self.run(*args, **kwargs)
    else:
      return_value = self.run(*args, **kwargs)
    self.settings = None
    return return_value