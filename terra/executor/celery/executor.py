# Based off of https://github.com/getninjas/celery-executor/
#
# Apache Software License 2.0
#
# Copyright (c) 2018, Alan Justino da Silva
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os import environ as env
from concurrent.futures import Future, Executor, as_completed
from concurrent.futures._base import (RUNNING, FINISHED, CANCELLED,
                                      CANCELLED_AND_NOTIFIED)
from threading import Lock, Thread
import time

from terra.logger import getLogger
logger = getLogger(__name__)


class CeleryExecutorFuture(Future):
  def __init__(self, asyncresult):
    self._ar = asyncresult
    super().__init__()

  def __del__(self):
    self._ar.forget()
    del self._ar

  def cancel(self):
    """Cancel the future if possible.
    Returns True if the future was cancelled, False otherwise. A future
    cannot be cancelled if it is running or has already completed.
    """
    with self._condition:
      if self._state in [RUNNING, FINISHED, CANCELLED, CANCELLED_AND_NOTIFIED]:
        return super().cancel()

      # Not running and not canceled. May be possible to cancel!
      self._ar.ready()  # Triggers an update check
      if self._ar.state != 'REVOKED':
        self._ar.revoke()
        self._ar.ready()

      # Celery task should be REVOKED now. Otherwise may be not possible
      # revoke it.
      if self._ar.state == 'REVOKED':
        result = super().cancel()
        if not result:  # pragma: no cover
          logger.error('Please open an issue on Github: Upstream '
                       'implementation changed?')
      else:
        # Is not running nor revoked nor finished :/
        # The revoke() had not produced effect: Task is probable not on a
        # worker, then not revoke-able.
        # Setting as RUNNING to inhibit super() from cancelling the Future,
        # then putting back.
        initial_state = self._state
        self._state = RUNNING
        result = super().cancel()
        if result:  # pragma: no cover
          logger.error('Please open an issue on Github: Upstream '
                       'implementation changed?')
        self._state = initial_state

      return result


class CeleryExecutor(Executor):
  """
  Executor implementation using celery tasks.

  Parameters
  ----------
  predelay
      Will trigger before the `.apply_async` internal call
  postdelay
      Will trigger before the `.apply_async` internal call
  applyasync_kwargs
      Options passed to the `.apply_async()` call
  retry_kwargs
      Options passed to the `.retry()` call on errors
  retry_queue
      Sugar to set an alternative queue specially for errors
  update_delay
      Delay time between checks for Future state changes
  """

  def __init__(self, predelay=None, postdelay=None, applyasync_kwargs=None,
               retry_kwargs=None, retry_queue='', update_delay=0.1,
               max_workers=None):
    # Options about calling the Task
    self._predelay = predelay
    self._postdelay = postdelay
    self._applyasync_kwargs = applyasync_kwargs or {}
    self._retry_kwargs = retry_kwargs or {}
    if retry_queue:
      self._retry_kwargs['queue'] = retry_queue
      self._retry_kwargs.setdefault('max_retries', 1)
    self._retry_kwargs.setdefault('max_retries', 0)

    # Options about managing this Executor flow
    self._update_delay = update_delay
    self._shutdown = False
    self._shutdown_lock = Lock()
    self._futures = set()
    self._monitor_started = False
    self._monitor_stopping = False
    self._monitor = Thread(target=self._update_futures)
    self._monitor.setDaemon(True)

  def _update_futures(self):
    while True:
      time.sleep(self._update_delay)  # Not-so-busy loop
      if self._monitor_stopping:
        return

      for fut in tuple(self._futures):
        if fut._state in (FINISHED, CANCELLED_AND_NOTIFIED):
          # This Future is set and done. Nothing else to do.
          self._futures.remove(fut)
          continue

        ar = fut._ar
        ar.ready()  # Just trigger the AsyncResult state update check

        if ar.state == 'REVOKED':
          logger.debug1('Celery task "%s" canceled.', ar.id)
          if not fut.cancelled():
            if not fut.cancel():  # pragma: no cover
              logger.error('Future was not running but failed to be cancelled')
            fut.set_running_or_notify_cancel()
          # Future is CANCELLED -> CANCELLED_AND_NOTIFIED

        elif ar.state in ('RUNNING', 'RETRY'):
          logger.debug1('Celery task "%s" running.', ar.id)
          if not fut.running():
            fut.set_running_or_notify_cancel()
          # Future is RUNNING

        elif ar.state == 'SUCCESS':
          logger.debug1('Celery task "%s" resolved.', ar.id)
          fut.set_result(ar.get(disable_sync_subtasks=False))
          # Future is FINISHED

        elif ar.state == 'FAILURE':
          logger.debug1('Celery task "%s" resolved with error.', ar.id)
          fut.set_exception(ar.result)
          # Future is FINISHED

        # else:  # ar.state in [RECEIVED, STARTED, REJECTED, RETRY]
        #     pass

  def submit(self, fn, *args, **kwargs):
    """
    """  # Original python comment has * and isn't napoleon compatible
    with self._shutdown_lock:
      if self._shutdown:
        raise RuntimeError('cannot schedule new futures after shutdown')

      if not self._monitor_started:
        self._monitor.start()
        self._monitor_started = True

      # metadata = {
      #     'retry_kwargs': self._retry_kwargs.copy()
      # }

      if self._predelay:
        self._predelay(fn, *args, **kwargs)
      # asyncresult = _celery_call.apply_async((fn, metadata) + args, kwargs,
      #                                        **self._applyasync_kwargs)
      asyncresult = fn.apply_async(args, kwargs)

      if self._postdelay:
        self._postdelay(asyncresult)

      future = CeleryExecutorFuture(asyncresult)
      self._futures.add(future)
      return future

  def shutdown(self, wait=True):
    with self._shutdown_lock:
      self._shutdown = True
      for fut in self._futures:
        fut.cancel()

    if wait:
      for _ in as_completed(self._futures):
        pass

      self._monitor_stopping = True
      try:
        self._monitor.join()
      except RuntimeError:  # pragma: no cover
        # Thread never started. Cannot join
        pass

  @staticmethod
  def configuration_map(service_info):
    from terra.compute import compute
    service_name = env['TERRA_CELERY_SERVICE']

    class ServiceClone:
      def __init__(self, service_info):
        self.compose_service_name = service_name

        if hasattr(service_info, 'justfile'):
          self.justfile = service_info.justfile
        if hasattr(service_info, 'compose_files'):
          self.compose_files = service_info.compose_files

        self.env = env  # .copy()
        self.volumes = []

    service_clone = ServiceClone(service_info)

    if hasattr(compute, 'config'):
      config = compute.config(service_clone)
    else:
      config = None

    volume_map = compute.get_volume_map(config, service_clone)

    # # In the case of docker, the config has /tmp_settings in there, this
    # # should be removed, as it is not in the celery worker. I don't think it
    # # would cause any problems, but it's inaccurate.
    # volume_map = [v for v in volume_map if v[1] != '/tmp_settings']

    return volume_map

    # optional_args = {}
    # optional_args['justfile'] = justfile

    # args = ["--wrap", "Just-docker-compose"] + \
    #     sum([['-f', cf] for cf in compose_files], []) + \
    #     ['config']

    # pid = just(*args, stdout=PIPE,
    #            **optional_args,
    #            env=service_info.env)
    # return pid.communicate()[0]
