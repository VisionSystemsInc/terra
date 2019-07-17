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

  The decorated function must have at least one argument named ``self``.
  ``self.status`` is injected into the ``self`` object, and can be used to read
  and write pieces of information to the ``status.json`` file

  Raises
  ------
  AlreadyRunException
      Thrown when function attempts to run a second time.
  '''

  def __inner_call__(self, *args, **kwargs):
    # Stages can only be run once, handle that
    try:
      if self.fun.already_run:
        raise AlreadyRunException("Already run")
    except AttributeError:
      pass
    self.fun.already_run = True

    # Get self of the wrapped function
    all_kwargs = args_to_kwargs(self.fun, args, kwargs)
    self.stage_self = all_kwargs['self']

    # Create a unique name fot the function
    stage_name = f'{inspect.getfile(self.fun)}//{self.fun.__qualname__}'

    # Load/create status file
    if not os.path.exists(settings.status_file):
      os.makedirs(os.path.dirname(settings.status_file), exist_ok=True)
      with open(settings.status_file, 'w') as fid:
        fid.write("{}")

    with open(settings.status_file, 'r') as fid:
      self.stage_self.status = ObjectDict(json.load(fid))

    # If resume is turned on
    if settings.resume:
      try:
        # Keep skipping until you match stage_name
        if self.stage_self.status.stage != stage_name:
          logger.debug(f"Skipping {stage_name}... "
                       f"Resuming to {self.stage_self.status.stage}")
          return None
        elif (self.stage_self.status.stage == stage_name
              # If it's wasn't done, it doesn't get skipped.
              and self.stage_self.status.stage_status == "done"):
          logger.debug(f"Skipping {stage_name}... "
                       f"Resuming after {self.stage_self.status.stage}")
          # The resume feature is done now, disable it so that everything else
          # can run
          settings.resume = False
          return None
      except AttributeError:
        pass
      # Set resume to false, so that this code isn't run again for this run.
      # - The resuming is done, so no need for the resume flag
      settings.resume = False

    # Log starting...
    self.stage_self.status.stage_status = "starting"
    self.stage_self.status.stage = stage_name
    logger.debug(f"Starting stage: {stage_name}")
    self.save_status()

    # Run function
    result = self.fun(*args, **kwargs)

    # Log done
    self.stage_self.status.stage_status = "done"
    logger.debug(f"Finished stage: {stage_name}")
    self.save_status()

    return result

  def save_status(self):
    '''
    Safe update the file
    '''

    shutil.move(settings.status_file, settings.status_file + '.bak')
    with open(settings.status_file, 'w') as fid:
      json.dump(self.stage_self.status, fid)
