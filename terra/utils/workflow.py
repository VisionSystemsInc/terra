'''
Utilities that will be used by apps
'''

import os
import shutil
import json
import inspect
from vsi.tools.python import BasicDecorator, args_to_kwargs

from terra.core.settings import ObjectDict
from terra import settings
from terra.logger import getLogger
logger = getLogger(__name__)


class AlreadyRunException(Exception):
  '''
  Exception thrown when a stage is run more than once. Stages are designed to
  be run only once
  '''


class resumable(BasicDecorator):
  '''
  Decorate for setting up a resumable stage in a workflow

  Simply using this decorator on a function makes that function a "stage" in
  the workflow. Stage execution is tracked in the
  :func:`terra.core.settings.status_file` and when using the
  ``settings.resume`` flag, will skip already run stages to attempt to pick up
  where a workflow left off.

  Resuming stages is good for failure cases, or situations where you want to
  skip the begining of a workflow

  Not every function in a workflow has to be a stage. These non-stage functions
  will always be run

  Raises
  ------
  AlreadyRunException
      Thrown when function attempts to run a second time.
  '''

  def __inner_call__(self, *args, **kwargs):
    try:
      if self.fun.already_run:
        raise AlreadyRunException("Already run")
    except AttributeError:
      pass

    self.fun.already_run = True

    all_kwargs = args_to_kwargs(self.fun, args, kwargs)
    stage_self = all_kwargs['self']

    stage_name = f'{inspect.getfile(self.fun)}//{self.fun.__qualname__}'

    if not os.path.exists(settings.status_file):
      try:
        os.makedirs(os.path.dirname(settings.status_file))
      except FileExistsError:
        pass
      with open(settings.status_file, 'w') as fid:
        fid.write("{}")

    with open(settings.status_file, 'r') as fid:
      stage_self.status = ObjectDict(json.load(fid))

    if settings.resume:
      try:
        if stage_self.status.stage != stage_name:
          logger.debug(f"Skipping {stage_name}... "
                       f"Resuming to {stage_self.status.stage}")
          return None
        elif stage_self.status.stage == stage_name \
            and stage_self.status.stage_status == "done":
          logger.debug(f"Skipping {stage_name}... "
                       f"Resuming after {stage_self.status.stage}")
          return None
      except AttributeError:
        pass
      settings.resume = False

    stage_self.status.stage_status = "starting"
    stage_self.status.stage = stage_name
    logger.debug(f"Starting: {stage_name}")

    result = self.fun(*args, **kwargs)

    stage_self.status.stage_status = "done"
    logger.debug(f"Finished: {stage_name}")

    shutil.move(settings.status_file, settings.status_file + '.bak')
    with open(settings.status_file, 'w') as fid:
      json.dump(stage_self.status, fid)

    return result
