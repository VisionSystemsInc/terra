import concurrent.futures
import terra.executor.base

__all__ = ['ProcessPoolExecutor']


class ProcessPoolExecutor(concurrent.futures.ProcessPoolExecutor,
                          terra.executor.base.BaseExecutor):
  multiprocess = True
