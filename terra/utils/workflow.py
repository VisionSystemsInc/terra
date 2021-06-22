'''
Utilities that will be used by apps
'''

import os
import shutil
import json
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

    # Create a unique name for the function
    stage_name = f'{self.fun.__module__}.{self.fun.__qualname__}'

    # Load/create status file
    if not os.path.exists(settings.status_file):
      os.makedirs(os.path.dirname(settings.status_file), exist_ok=True)
      with open(settings.status_file, 'w') as fid:
        fid.write("{}")

    with open(settings.status_file, 'r') as fid:
      self.status = ObjectDict(json.load(fid))

    temporary_overwrite = False

    # If resume is turned on
    if settings.resume:
      try:
        # If the stage is done, skip it
        if self.status[stage_name].state == "done":
          logger.debug(f"Skipping {stage_name} (settings.resume == true, "
                       "and stage is marked as already done)")
          return None
        # the stage is being re-run, so we're going to set overwrite to True
        else:
          temporary_overwrite = True
      except (KeyError, AttributeError):
        pass

    # reset stage info
    self.status[stage_name] = ObjectDict({
        "name": stage_name,
        "state": None,
    })

    # add current stage status to stage_self.status
    self.stage_self.status = self.status[stage_name]

    # Log starting...
    self.status[stage_name].state = "starting"
    logger.debug(f"Starting stage: {stage_name}")
    self.save_status()

    # Run function
    if temporary_overwrite:
      # If we are resuming a broken stage, then temporarily set overwrite to
      # True
      logger.info(f"Resuming stage: {stage_name}, temporarily setting "
                  "overwrite to True.")
      with settings:
        settings.overwrite = True
        result = self.fun(*args, **kwargs)
    else:
      result = self.fun(*args, **kwargs)

    # Log done
    self.status[stage_name].state = "done"
    logger.debug(f"Finished stage: {stage_name}")
    self.save_status()

    return result

  def save_status(self):
    '''
    Safe update the file
    '''
    logger.debug4(f"status: {self.status}")
    logger.debug4(f"stage.status: {self.stage_self.status}")

    shutil.move(settings.status_file, settings.status_file + '.bak')
    with open(settings.status_file, 'w') as fid:
      json.dump(self.status, fid)
