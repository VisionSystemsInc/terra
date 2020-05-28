'''
Demo app that tests if a terra config is working

*** WARNING *** This will spin up real computers and workers, if you are
configured to do so. May result in a small amount of billing.
'''

from terra.utils.cli import ArgumentParser
from terra import settings
from terra.logger import getLogger
logger = getLogger(__name__)


def main(args=None):
  settings.terra.zone
  logger.critical('Demo 1')


if __name__ == '__main__':
  ArgumentParser().parse_args()
  main()
