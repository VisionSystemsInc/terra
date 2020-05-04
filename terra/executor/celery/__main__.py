#!/usr/bin/env python

from os import environ as env
from . import app

# Terra
from terra import settings


def main():
  if env.get('TERRA_SETTINGS_FILE', '') == '':
    print('SGR - default settings')

    settings.configure(
      {
        'executor': {'type': 'CeleryExecutor'},
        # FIXME
        'terra': {'zone': 'task'},
        #'terra': {'zone': 'task_controller'},
        'logging': {'level': 'NOTSET'}
      }
    )
  print('SGR - celery.__main__.py')

  # REVIEW are settings setup at this point; they must be setup before the
  # celery tasks start

  app.start()

if __name__ == '__main__':  # pragma: no cover
  main()
