#!/usr/bin/env python

from os import environ as env
from . import app, setup_task_controller
import tempfile
import warnings

# Terra
from terra import settings


def main():
  if env.get('TERRA_SETTINGS_FILE', '') == '':
    warnings.warn("terra.executor.celery.__main__ shouldn't be needed "
                  "anymore. When calling celery, use "
                  "'-A terra.executor.celery.app'", DeprecationWarning)
    setup_task_controller()
  app.start()


if __name__ == '__main__':  # pragma: no cover
  main()
