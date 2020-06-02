import sys
from os import environ as env

from celery.signals import worker_process_init
from celery import Celery

from .executor import CeleryExecutor
from terra.logger import getLogger
logger = getLogger(__name__)

__all__ = ['CeleryExecutor']


main_name = env.get('TERRA_CELERY_MAIN_NAME', None)
if main_name is None:
  try:
    main_name = sys.modules['__main__'].__spec__.name
  except AttributeError:
   # if __spec__ is None, then __main__ is a builtin
    main_name = "main_name_unset__set_TERRA_CELERY_MAIN_NAME"
app = Celery(main_name)

app.config_from_object(env['TERRA_CELERY_CONF'])


@worker_process_init.connect
def start_worker_child(*args, **kwargs):
  from terra import settings
  settings.terra.zone = 'task'

# Running on windows.
# https://stackoverflow.com/questions/37255548/how-to-run-celery-on-windows
