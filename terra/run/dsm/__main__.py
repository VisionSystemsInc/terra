import argparse

from terra.dsm import GenerateDsm
from os import environ as env

def get_parser():
  parser = argparse.ArgumentParser(description="Terra Main Runner")
  aa = parser.add_argument
  aa('config', type=str, help="config.json filename")
  return parser

def main(args=None):
  args = get_parser().parse_args(args)
  env['TERRA_SETTINGS_FILE'] = args.config
  dsm = GenerateDsm()
  dsm.generate_dsm()

if __name__ == '__main__':
  main()