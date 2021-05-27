#!/usr/bin/env python

from os import environ as env
from . import app
import tempfile

# Terra
from terra import settings


def main():
  if env.get('TERRA_SETTINGS_FILE', '') == '':
    settings.configure(
      {
        'executor': {'type': 'CeleryExecutor'},
        'terra': {'zone': 'task_controller'},
        'logging': {'level': 'NOTSET'},
        'processing_dir': tempfile.mkdtemp(prefix="terra_celery_"),
      }
    )

  app.start()


if __name__ == '__main__':  # pragma: no cover
  main()
