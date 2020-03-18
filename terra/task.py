from os import environ as env

from celery import Task, shared_task as original_shared_task

__all__ = ['TerraTask', 'shared_task']

def shared_task(*args, **kwargs):
  kwargs['bind'] = True
  kwargs['base'] = TerraTask
  return original_shared_task(*args, **kwargs)

class TerraTask(Task):
  @staticmethod
  def _patch_settings(args, kwargs):
    if 'TERRA_EXECUTOR_SETTINGS_FILE' in env:
      # TODO: Cache loads for efficiency?
      settings = json.load(env['TERRA_EXECUTOR_SETTINGS_FILE'])

      # If args is not empty, the first arg was settings
      if args:
        args[0] = settings
      else:
        kwargs['settings'] = settings

  def apply_async(self, args=None, kwargs=None, task_id=None, user=None,
                  *args2, **kwargs2):
    TerraTask._patch_settings(args, kwargs)
    return super().apply_async(args=args, kwargs=kwargs,
                               task_id=task_id, *args2, **kwargs2)

  def apply(self, *args, **kwargs):
    TerraTask._patch_settings(args, kwargs)
    return super().apply(*args, **kwargs)
