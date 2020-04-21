#!/usr/bin/env python

import sys
from os import environ as env

from celery import Celery

from .executor import CeleryExecutor
from terra.logger import getLogger
logger = getLogger(__name__)

__all__ = ['CeleryExecutor']


main_name = env.get('TERRA_CELERY_MAIN_NAME', None)
if main_name is None:
  try:
    main_name = sys.modules['__main__'].__spec__.name
  except:
    main_name = "main_name_unset_Set_TERRA_CELERY_MAIN_NAME"
app = Celery(main_name)

app.config_from_object(env['TERRA_CELERY_CONF'])

# app.running = False
# from celery.signals import worker_process_init
# @worker_process_init.connect
# def set_running(*args, **kwargs):
#     app.running = True

# import traceback
# traceback.print_stack()

# Running on windows.
# https://stackoverflow.com/questions/37255548/how-to-run-celery-on-windows

if __name__ == '__main__':  # pragma: no cover
  app.start()
