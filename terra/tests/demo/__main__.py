'''
Demo app that tests if a terra config is working

*** WARNING *** This will spin up real computers and workers, if you are
configured to do so. May result in a small amount of billing.
'''

from os import environ as env
import tempfile
import os
import json
import pydoc

from terra import settings
from terra.core.settings import ENVIRONMENT_VARIABLE, settings_property
from terra.core.exceptions import ImproperlyConfigured
from terra.utils.cli import FullPaths, ArgumentParser

@settings_property
def singularity_unset(self):
  raise ImproperlyConfigured('You must to set --compose and --service for '
                             'singularity')

def demo_templates():
  docker = {
    "demo": {"compose": os.path.join(env['TERRA_TERRA_DIR'],
                                     'docker-compose-main.yml'),
             "service": "terra-demo"}
  }

  singularity = {
    "demo": {"compose": singularity_unset,
             "service": singularity_unset}
  }

  templates = [
    ({"compute": {"arch": "docker"}}, docker),
    ({"compute": {"arch": "terra.compute.docker"}}, docker),
    ({"compute": {"arch": "singularity"}}, singularity),
    ({"compute": {"arch": "terra.compute.singularity"}}, singularity)
  ]
  return templates


def get_parser():
  parser = ArgumentParser(description="View Angle Runner")
  aa = parser.add_argument
  aa('--loglevel', type=str, help="Log level", default=None)
  aa('--compose', type=str, default=None,
     help="Compose filename (for docker/singularity)")
  aa('--service', type=str, default=None,
     help="Service name (for docker/singularity)")
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
  settings_json['demo'] = {}

  if args.compose:
    settings_json['demo']['compose'] = args.compose
  if args.service:
    settings_json['demo']['service'] = args.service
  if args.loglevel:
    try:
      settings_json['logging']['level'] = args.loglevel
    except KeyError:
      settings_json['logging'] = {'level': args.loglevel}

  # Configure settings
  settings.add_templates(demo_templates())
  settings.configure(settings_json)

  # import pprint
  # pprint.pprint(settings)

  # Run workflow
  from .workflows import DemoWorkflow
  DemoWorkflow().demonate()


if __name__ == '__main__':
  processing_dir = tempfile.TemporaryDirectory()
  try:
    main(processing_dir.name)
    # with open(os.path.join(processing_dir.name, 'terra_log'), 'r') as fid:
    #   print('-------------------')
    #   print('Paging log messages')
    #   print('-------------------')
    #   pydoc.pager(fid.read())
  finally:
    processing_dir.cleanup()
