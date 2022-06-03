import argparse
import os
import ast
from os import environ as env

from terra.utils.cli import FullPaths, clean_path


class CreateTerraApp:
  def __init__(self, app_camel_name, module_path, camel_name, under_name,
               dir_name,):
    self.app_camel_name = app_camel_name
    self.module_path = module_path
    self.dir = dir_name

    self.camel_name = camel_name
    self.under_name = under_name

    terra_apps = ast.literal_eval(env['TERRA_APP_PREFIXES_AST'])
    self.app_prefix = terra_apps[0]

  def generate_files(self):
    os.makedirs(os.path.join(self.dir, 'service_runners'), exist_ok=True)
    os.makedirs(os.path.join(self.dir, 'tasks'), exist_ok=True)
    os.makedirs(os.path.join(self.dir, 'tests'), exist_ok=True)

    for create_file in [self.init, self.cli,
                        self.workflows,
                        self.service_definitions,
                        self.service_runners_init,
                        self.service_runners,
                        self.tasks_init,
                        self.tasks]:
      try:
        create_file()
      except FileExistsError as fee:
        print(f'{fee.filename} already exists, skipping')

  def init(self):
    with open(os.path.join(self.dir, '__init__.py'), 'x') as fid:
      fid.write(r'''# Example: You would disable warnings for this app here.

#import logging
#import warnings

#from terra.logger import _demoteLevel, DEBUG1, DEBUG4
#import terra.core.signals

## suppress specific warnings from pvl
#warnings.filterwarnings("ignore", category=PendingDeprecationWarning,
#                        module='pvl', message=r".*pvl\.collections\.Units.*")
#warnings.filterwarnings("ignore", category=ImportWarning,
#                        module='pvl', message=r".*PVLMultiDict.*")

#terra.core.signals.logger_configure.connect(
#    lambda *args, **kwargs: _demoteLevel(('shapely.geos',), DEBUG1, DEBUG4),
#    weak=False)
''')

  def cli(self):
    with open(os.path.join(self.dir, '__main__.py'), 'x') as fid:
      fid.write(f'''import os
import sys
from os import environ as env
import glob

from {self.module_path}.workflows import {self.camel_name}Workflow

from terra import settings
from terra.core.settings import settings_property
from terra.logger import getLogger
from terra.utils.cli import FullPaths, ArgumentParser

logger = getLogger(__name__)

def get_parser():
  parser = ArgumentParser(description="{self.app_camel_name} Runner")
  aa = parser.add_argument
  aa('settings', type=str, help="JSON settings file", action=FullPaths)
  return parser

@settings_property
def some_thing_dir(self):
  return os.path.join(self.processing_dir, 'some_thing')

{self.app_camel_name.lower()}_templates = [
  (
    {{}},
    {{
      "parameter_alpha": 1.2,
      "service_dirs": {{
        "{self.under_name}_dir": some_thing_dir,
      }}
    }}
  )
]

def main(args=None):
  args = get_parser().parse_args(args)
  env['TERRA_SETTINGS_FILE'] = args.settings
  settings.add_templates({self.app_camel_name.lower()}_templates)

  {self.app_camel_name.lower()} = {self.camel_name}Workflow()
  {self.app_camel_name.lower()}.run()


if __name__ == '__main__':
  main()
''')  # noqa: E501

  def workflows(self):
    with open(os.path.join(self.dir, 'workflows.py'), 'x') as fid:
      fid.write(f'''from terra import settings
from terra.compute import compute
from terra.utils.workflow import resumable
from terra.workflow import PipelineWorkflow
from terra.logger import getLogger
logger = getLogger(__name__)


class {self.camel_name}Workflow(PipelineWorkflow):
  def __init__(self):
    services = [self.{self.camel_name}]

    # if settings.parameter_alpha > 2:
    #   services += [self.foobar]

    self.pipeline = [*services]

  @resumable
  def {self.camel_name}(self):
    compute.run('{self.module_path}.service_definitions.{self.camel_name}')
''')

  def service_definitions(self):
    source_dir_docker = env[self.app_prefix + '_SOURCE_DIR_DOCKER']

    with open(os.path.join(self.dir, 'service_definitions.py'), 'x') as fid:
      fid.write(f'''from os import environ as env
import os
import posixpath

# Terra settings
from terra import settings

# Terra compute architectures
from terra.compute.virtualenv import (
  Service as VenvService,
  Compute as VenvCompute
)
from terra.compute.docker import (
  Service as DockerService,
  Compute as DockerCompute
)
from terra.compute.singularity import (
  Service as SingularityService,
  Compute as SingularityCompute
)

# Terra base service definition
from terra.compute.base import BaseService
from terra.compute.container import ContainerService

# Terra logger
from terra.logger import getLogger
logger = getLogger(__name__)


###############################################################################
#                              COMMON SERVICES                                #
###############################################################################

{self.app_camel_name.lower()}_mount_points = {{

    # current processing & service directory
    "processing_dir": "/processing",

    "image_dir": "/image",

    # service directories
    "{self.under_name}_dir": "/{self.app_camel_name.lower()}/some_thing",
}}


class {self.app_camel_name}BaseService(BaseService):
  justfile = os.path.join(env.get('{self.app_prefix}_SOURCE_DIR', '{source_dir_docker}'), 'Justfile')

  def pre_run(self):
    self.service_dir = getattr(settings.service_dirs, self.service_dir_key)

    # self.add_volume(self.service_dir, {self.app_camel_name.lower()}_mount_points[self.service_dir_key])

    super().pre_run()


class {self.app_camel_name}VenvService({self.app_camel_name}BaseService, VenvService):
  pass


class {self.app_camel_name}ContainerService({self.app_camel_name}BaseService, ContainerService):
  compose_service_name = env['{self.app_prefix}_COMPOSE_SERVICE_RUNNER']


class {self.app_camel_name}DockerService({self.app_camel_name}ContainerService, DockerService):
  def __init__(self):
    super().__init__()

    # default docker-compose files
    self.compose_files = [
        os.path.join(env['{self.app_prefix}_SOURCE_DIR'], 'docker-compose.yml'),
    ]


class {self.app_camel_name}SingularityService({self.app_camel_name}ContainerService, SingularityService):
  def __init__(self):
    super().__init__()

    # default singular-compose files
    self.compose_files = [
        os.path.join(env['{self.app_prefix}_SOURCE_DIR'], 'singular-compose.env'),
    ]


###############################################################################
#                            Some Service                                     #
###############################################################################
class {self.camel_name}({self.app_camel_name}BaseService):
  service_dir_key = '{self.under_name}_dir'
  command = ['python', '-m', '{self.module_path}.service_runners.{self.under_name}']


class {self.camel_name}_container({self.camel_name},
                            {self.app_camel_name}ContainerService):
  def __init__(self):
    super().__init__()

    # self.add_volume(settings.image_dir,
    #                 {self.app_camel_name.lower()}_mount_points['image_dir'], 'ro')


@VenvCompute.register({self.camel_name})
class {self.camel_name}_Venv({self.camel_name}, {self.app_camel_name}VenvService):
  pass


@DockerCompute.register({self.camel_name})
class {self.camel_name}_docker({self.camel_name}_container,
                         {self.app_camel_name}DockerService):
  pass


@SingularityCompute.register({self.camel_name})
class {self.camel_name}_singular({self.camel_name}_container,
                           {self.app_camel_name}SingularityService):
  pass
''')  # noqa: E501

  def service_runners_init(self):
    with open(os.path.join(self.dir, 'service_runners',
                           '__init__.py'), 'x') as fid:
      fid.write('')

  def service_runners(self):
    with open(os.path.join(self.dir, 'service_runners',
                           f'{self.under_name}.py'), 'x') as fid:
      fid.write(f'''import concurrent.futures

from terra import settings
from terra.executor import Executor

from {self.module_path}.tasks.{self.under_name} import {self.under_name}_in_parallel

from terra.logger import getLogger
logger = getLogger(__name__)

def yield_{self.under_name}_futures(executor, xs, ys):
  for x in xs:
    for y in ys:
      future = executor.submit({self.under_name}_in_parallel, x=x, y=y)
      yield (future, (x,y))

def main():
  # Actual algorithm goes here. Here's an example that uses parallelism
  logger.critical('test')
  with Executor(max_workers=settings.executor.num_workers) as executor:
    futures_to_task = {{future: task_id for future, task_id in yield_{self.under_name}_futures(executor, (1,2), (10, 20))}}

    for future in concurrent.futures.as_completed(futures_to_task):
      x,y = futures_to_task[future]
      logger.info(f"{{x}} + {{y}} = {{future.result()}}")

if __name__ == '__main__':
  main()
''')  # noqa: E501

  def tasks_init(self):
    with open(os.path.join(self.dir, 'tasks', '__init__.py'), 'x') as fid:
      fid.write('')

  def tasks(self):
    with open(os.path.join(self.dir, 'tasks', f'{self.under_name}.py'), 'x') \
        as fid:
      fid.write(f'''from terra.task import shared_task

# Terra core
from terra.logger import getLogger
logger = getLogger(__name__)

@shared_task
def {self.under_name}_in_parallel(self, x, y):
  return x+y
''')  # noqa: E501


def get_parser():
  parser = argparse.ArgumentParser()
  parser.add_argument('--AppName', type=str, dest='app_name',
                      default='AppName', help="Name of app to create a "
                      "template for, should be CamelCase")
  parser.add_argument('--module.path', type=str, dest='module_path',
                      required=True, help="The module path (i.e. python path "
                      "syntax) of the module you are setting up: e.g. "
                      "'foo.bar'")
  parser.add_argument('--dir', default=clean_path('.'), type=str,
                      action=FullPaths, help="The directory to create the "
                      "template in. Defaults to the current directory")
  parser.add_argument('--name', default="do something", type=str,
                      help="String to generate the workflow/service/task name:"
                      " e.g. 'calculate threshold'")
  return parser


def main(args=None):
  args = get_parser().parse_args(args)
  Name = args.name.title().replace(' ', '')
  name = args.name.lower().replace(' ', '_')
  create_terra_app = CreateTerraApp(args.app_name, args.module_path,
                                    Name, name, args.dir)
  create_terra_app.generate_files()

  print('''Here's an example config file to use:

{
  "logging": {
    "level": "DEBUG3"
  },
  "compute": {
    "arch": "docker"
  }
}

''')

  print(f'Simply run: just run {args.module_path} that_config_file.json')


if __name__ == '__main__':
  main()
