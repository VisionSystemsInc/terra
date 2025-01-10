from argparse import _AppendAction, _copy_items

from terra import settings
from terra.workflow import SingleWorkflow
from terra.logger import getLogger
from terra.utils.cli import FullPaths, ArgumentParser, resolve_path

logger = getLogger(__name__)


class FullPathsPairAppend(_AppendAction):
  def __call__(self, parser, namespace, values, option_string=None):
    items = _copy_items(getattr(namespace, self.dest, None))
    items.append([resolve_path(values[0]), values[1]])
    setattr(namespace, self.dest, items)


def get_parser():
  parser = ArgumentParser(
    description="Generic CLI to execute a Service Runner")
  aa = parser.add_argument
  aa('--output', type=str, default=None, action=FullPaths)
  aa('--shell', default=False, action='store_true')
  aa('--mount', default=[], nargs=2, action=FullPathsPairAppend)
  aa('--mountro', default=[], nargs=2, action=FullPathsPairAppend)
  aa('--service', default='runner', type=str)
  aa('command', default=[], nargs='*')

  return parser


generic_templates = [
  (
    {},
    {
      "shell": False,
      "command": ["python"],
      "compute": {
        "arch": "docker"
      },
      "compose_service": "runner",
      "mounts": [],
      "mountsro": []
    }
  )
]


def main(args=None):
  args = get_parser().parse_args(args)

  config = {}
  config['shell'] = args.shell
  config['command'] = args.command
  config['compose_service'] = args.service
  if args.output:
    config['processing_dir'] = args.output
  config['mounts'] = args.mount
  config['mountsro'] = args.mountro
  settings.add_templates(generic_templates)

  # fileless configure
  settings.configure(config)

  generic = SingleWorkflow('terra.generic.definitions.Generic')
  generic.run()


if __name__ == '__main__':
  main()
