#!/usr/bin/env python

from os import environ as env
from . import app

# Terra
from terra import settings


def main():
  if env.get('TERRA_SETTINGS_FILE', '') == '':
    settings.configure(
      {
        'executor': {'type': 'CeleryExecutor'},
        'terra': {'zone': 'task_controller'},
        'logging': {'level': 'INFO'}
        # 'logging': {'level': 'NOTSET'}
      }
    )
  # REVIEW are settings setup at this point; they must be setup before the
  # celery tasks start

  app.start()

if __name__ == '__main__':  # pragma: no cover
  main()
