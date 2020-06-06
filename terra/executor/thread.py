import concurrent.futures

import terra.executor.base
import terra.core.settings

__all__ = ['ThreadPoolExecutor']


class ThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor,
                         terra.executor.base.BaseExecutor):
  def __init__(self, *args, **kwargs):
    # Make terra.setting "thread safe"
    if not isinstance(terra.settings,
                      terra.core.settings.LazySettingsThreaded):
      terra.core.settings.LazySettingsThreaded.downcast(terra.settings)
    super().__init__(*args, **kwargs)
