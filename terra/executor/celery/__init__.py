import sys
import platform
from os import environ as env
import tempfile

from celery.signals import worker_process_init, celeryd_init, setup_logging
from celery import Celery
from celery.utils.nodenames import node_format

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


# stop celery from hijacking the logger
@setup_logging.connect
def setup_loggers(*args, **kwargs):
  pass


@celeryd_init.connect
def setup_task_controller(*args, **kwargs):
  from terra import settings

  if env.get('TERRA_SETTINGS_FILE', '') == '':
    temp_config = {'executor': {'type': 'CeleryExecutor'},
                   'terra': {'zone': 'task_controller'},
                   'logging': {'level': 'NOTSET'},
                   'processing_dir': tempfile.mkdtemp(prefix="terra_celery_")}

    # This won't cover 100% of ways that celery can set the logfile/hostname,
    # but it covers one optional way, that works for celery multi calls
    logfile = [x for x in sys.argv if x.startswith('--logfile')]
    if logfile:
      # Celery args must have = in them 🤷‍♂️
      logfile = logfile[0].split('=', 1)[1]
      logfile = node_format(logfile, platform.node())
      temp_config['logging']['log_file'] = logfile

    settings.configure(temp_config)


@worker_process_init.connect
def start_worker_child(*args, **kwargs):
  from terra import settings
  settings.terra.zone = 'task'

# Running on windows.
# https://stackoverflow.com/questions/37255548/how-to-run-celery-on-windows
