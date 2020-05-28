import concurrent.futures
import terra.executor.base

__all__ = ['ThreadPoolExecutor']


class ThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor,
                         terra.executor.base.BaseExecutor):
  pass
