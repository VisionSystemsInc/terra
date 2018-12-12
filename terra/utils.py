import os
import json
import inspect
from vsi.tools.python import BasicDecorator, args_to_kwargs

from terra.logger import getLogger
logger = getLogger(__name__)

from terra.core.settings import ObjectDict
from terra import settings

class resumable(BasicDecorator):
  def __inner_call__(self, *args, **kwargs):
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
      except AttributeError:
        pass
      settings.resume = False

    stage_self.status.stage_status = "starting"
    stage_self.status.stage = stage_name
    logger.debug(f"Starting: {stage_name}")

    result = self.fun(*args, **kwargs)

    stage_self.status.stage_status = "done"
    logger.debug(f"Finished: {stage_name}")

    os.rename(settings.status_file, settings.status_file+'.bak')
    with open(settings.status_file, 'w') as fid:
      json.dump(stage_self.status, fid)

    return result