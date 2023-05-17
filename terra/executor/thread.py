import concurrent.futures
import traceback

import terra.executor.base
import terra.core.settings

__all__ = ['ThreadPoolExecutor']


def auto_clear_exception_frames(future):
  exc = future.exception()
  if exc is not None:
    traceback.clear_frames(exc.__traceback__)


class ThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor,
                         terra.executor.base.BaseExecutor):
  '''
  Terra version of :class:`concurrent.futures.ThreadPoolExecutor`

  Unlike other executors, :class:`ThreadPoolExecutor` has no process isolation.
  This results in a scenario where multiple threads could use terra settings to
  influence each other, which is not typical behavior, given that all other
  executors have process isolation and do not allow this.

  :class:`ThreadPoolExecutor` will downcast :obj:`terra.core.settings` to a
  thread-safe :class:`terra.core.settings.LazySettingsThreaded` where each
  Executor thread has it's own thread local storage version of the settings
  structure.

  This behavior is limited to threads started by :class:`ThreadPoolExecutor`
  only. All other threads will have normal thread behavior with the runner
  threads, and use a single version of the settings. The only side effect is if
  a task starts its own thread, it will be treated as one of the runner
  threads, not a task thread. The currently known downside to this is log
  messages will be reported as coming from the runner rather than task zone.
  However, any attempts to edit settings from this rogue thread could
  potentially have other unintended consequences.
  '''

  def __init__(self, *args, **kwargs):
    # Make terra.setting "thread safe"
    if not isinstance(terra.settings,
                      terra.core.settings.LazySettingsThreaded):
      terra.core.settings.LazySettingsThreaded.downcast(terra.settings)
    super().__init__(*args, **kwargs)

  def submit(self, fn, *args, **kwargs):
    future = super().submit(fn, *args, **kwargs)
    future.add_done_callback(auto_clear_exception_frames)
    return future
