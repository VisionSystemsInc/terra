import concurrent.futures
from multiprocessing import get_context

import terra.executor.base

__all__ = ['ProcessPoolExecutor']


class ProcessPoolExecutor(concurrent.futures.ProcessPoolExecutor,
                          terra.executor.base.BaseExecutor):
  multiprocess = True

  def __init__(self, *args, **kwargs):
    # Workaround for https://github.com/VisionSystemsInc/terra/issues/115 the
    # simplest workaround was to pre-finalize celery and pre-cache the property
    # app.tasks, as these were the components with locks that were causing
    # deadlocks
    from celery import _state
    _state.get_current_app().tasks
    return super().__init__(*args, **kwargs)

class ProcessPoolExecutorSpawn(ProcessPoolExecutor):
  def __init__(self, *args, **kwargs):
    kwargs['mp_context'] = get_context('spawn')
    return super().__init__(*args, **kwargs)
