'''
Demo app that tests if a terra config is working

*** WARNING *** This will spin up real computers and workers, if you are
configured to do so. May result in a small amount of billing.
'''

import concurrent.futures

from terra.tests.demo.tasks import demo2
from terra.utils.cli import ArgumentParser
from terra.executor import Executor
from terra import settings
from terra.logger import getLogger
logger = getLogger(__name__)


def main(args=None):
  settings.terra.zone
  logger.critical('Demo 2 Starting')

  futures = {}

  with Executor(max_workers=4) as executor:
    for x in range(1, 3):
      for y in range(4, 6):
        futures[executor.submit(demo2, x, y)] = (x, y)

    for future in concurrent.futures.as_completed(futures):
      logger.info(f'Completed: {settings.terra.zone} {futures[future]}')

  logger.critical('Demo 2 Done')


if __name__ == '__main__':
  ArgumentParser().parse_args()
  main()
