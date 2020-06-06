import concurrent.futures

import terra.executor.base
import terra.core.settings

__all__ = ['ThreadPoolExecutor']


class ThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor,
                         terra.executor.base.BaseExecutor):
  '''
  Terra version of :class:`concurrent.futures.ThreadPoolExecutor`

  Unlike other executors, :class:`ThreadPoolExecutor` has no process isolation.
  This results in a scenario where multiple threads could be terra settings,
  actually influence each other, which is not typical behavior, given that
  all other executors have process isolation and do not allow this.

  :class:`ThreadPoolExecutor` will downcast :obj:`terra.core.settings` to a
  thread-safe :class:`terra.core.settings.LazySettingsThreaded` where each
  Executor thread has it's own thread local storage version of the settings
  structure.

  This behavior is limited to threads started by ThreadPoolExecutor only. All
  other threads will have normal thread behavior with the runner threads, and
  use a single version of the settings. The only side effect is if a task
  starts its own thread, it will be treated as one of the runner threads, not a
  task thread. The currently known downside to this is log messages will be
  reported as coming from the runner rather than task zone. However, any
  attempts to edit settings from this rouge thread can have unintended
  consequences.
  '''

  def __init__(self, *args, **kwargs):
    # Make terra.setting "thread safe"
    if not isinstance(terra.settings,
                      terra.core.settings.LazySettingsThreaded):
      terra.core.settings.LazySettingsThreaded.downcast(terra.settings)
    super().__init__(*args, **kwargs)
