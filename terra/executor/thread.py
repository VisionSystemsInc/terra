import concurrent.futures
import concurrent.futures.thread
import weakref
import threading

import terra.executor.base

__all__ = ['ThreadPoolExecutor']


class ThreadPoolExecutor(concurrent.futures.ThreadPoolExecutor,
                         terra.executor.base.BaseExecutor):
  # This function works in python 3.6-3.9
  def _adjust_thread_count(self):
    # 3.8 compatibility
    if hasattr(self, '_idle_semaphore'):
      # if idle threads are available, don't spin new threads
      if self._idle_semaphore.acquire(timeout=0):
        return
    # When the executor gets lost, the weakref callback will wake up
    # the worker threads.
    def weakref_cb(_, q=self._work_queue):
      q.put(None)
    num_threads = len(self._threads)
    if num_threads < self._max_workers:
      thread_name = '%s_%d' % (self._thread_name_prefix or self, num_threads)
      args = (weakref.ref(self, weakref_cb), self._work_queue)
      # 3.7 compatibility
      if hasattr(self, '_initializer'):
        args += (self._initializer, self._initargs)
      t = threading.Thread(name=thread_name,
                           target=concurrent.futures.thread._worker,
                           args=args)
      t.daemon = True
      self._threads.add(t)
      concurrent.futures.thread._threads_queues[t] = self._work_queue
      # Start thread AFTER adding it to the queue, so any check to see if
      # current thread is in _threads_queues work correctly.
      t.start()