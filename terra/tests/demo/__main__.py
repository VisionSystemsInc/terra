'''
Demo app that tests if a terra config is working

*** WARNING *** This will spin up real computers and workers, if you are
configured to do so. May result in a small amount of billing.
'''

import argparse
from os import environ as env
import tempfile
import os
import json
import pydoc

from terra import settings
from terra.core.settings import ENVIRONMENT_VARIABLE
from terra.utils.cli import FullPaths


def get_parser():
  parser = argparse.ArgumentParser(description="View Angle Runner")
  aa = parser.add_argument
  aa('--loglevel', type=str, help="Log level", default=None)
  aa('settings', type=str, help="JSON settings file",
     default=os.environ.get(ENVIRONMENT_VARIABLE), action=FullPaths)
  return parser


def main(processing_dir, args=None):
  args = get_parser().parse_args(args)

  # Load settings
  with open(args.settings, 'r') as fid:
    settings_json = json.load(fid)

  # Patch settings for demo
  settings_json['processing_dir'] = processing_dir
  if args.loglevel:
    try:
      settings_json['logging']['level'] = args.loglevel
    except KeyError:
      settings_json['logging'] = {'level': args.loglevel}

  # Configure settings
  settings.configure(settings_json)

  import pprint
  pprint.pprint(settings)

  # Run workflow
  from .workflows import DemoWorkflow
  DemoWorkflow().demonate()

  import terra.logger
  print(terra.logger._logs.tcp_logging_server.ready)



if __name__ == '__main__':
  processing_dir = tempfile.TemporaryDirectory()
  try:
    main(processing_dir.name)
    with open(os.path.join(processing_dir.name, 'terra_log'), 'r') as fid:
      print('-------------------')
      print('Paging log messages')
      print('-------------------')
      pydoc.pager(fid.read())
  finally:
    processing_dir.cleanup()
