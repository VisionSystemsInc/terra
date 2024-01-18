from os import environ as env
from subprocess import Popen, PIPE
from functools import partial

from terra import settings
import terra.core.signals
from terra.logger import getLogger

logger = getLogger(__name__)


def log_terra_version(sender, signal, app_name=None, terra_prefix=None,
                      **kwargs):
  '''
  Log the version of Terra App

  Uses the :data:`logger configured dispatcher
  <terra.core.signals.logger_configure>` to log the Terra App version used to
  create the environment. Since this can be a complicated mixture of code
  versions, the Terra App version is logged by the main controller and by each
  service runner. This will capture a wide array of scenarios from development
  environment to fully containerized deploy.

  Keyword Arguments
  -----------------
  app_name : :obj:`str`
    Name of app that appears in the logs
  terra_prefix : :obj:`str`
    Name of environment variable prefix used


  The following environment variables are needed to determine the git commit:

  Attributes
  ----------
  {terra_prefix}_IMAGE_COMMIT : :obj:`str`
    This should be set in the container image, and should be the output of
    ``git describe --all --long --always --dirty``.
  {terra_prefix}_DEPLOY_COMMIT : :obj:`str`
    This should be set in the deploy image, and should be the output of
    ``git describe --all --long --always --dirty``.
  {terra_prefix}_CWD : :obj:`str`
    The location of the app source code directory, for use in development
    environment to determine the current git commit.


  A typical log will include these lines to tell you what version is running:

  .. code-block::

     2024-01-11 08:39:53,820 (computer.example.com:controller): INFO/MainProcess - __init__.py - Terra AppName version: heads/main-0-g5e17bc5
     ...
     2024-01-11 08:40:03,382 (13ab62e95a44:runner): INFO/MainProcess - __init__.py - Terra AppName Runner version: heads/main-0-g5e17bc5

  Examples
  --------

  Details in the versions can be used to interpret a variety of situations,
  such as:

  - Development environment synced and running on main (as shown above):

    - ``Terra AppName version: heads/main-0-g5e17bc5``
    - ``Terra AppName Runner version: heads/main-0-g5e17bc5``

  - Development environment where `just sync` was run off of main, but then
    files were modified but not committed when running

    - ``Terra AppName version: heads/main-0-g5e17bc5``
    - ``Terra AppName Runner version: heads/main-0-g5e17bc5-dirty``

  - Development environment where ``just sync`` was run off sha 7b227ce, but
    then a different commit was used when running

    - ``Terra AppName version: heads/example_branch-0-g7b227ce``
    - ``Terra AppName Runner version: heads/example_branch-0-g305bcbb``

  - Fully containerized:

    - ``Terra AppName Deploy version: heads/main-0-g5e17bc5``
    - ``Terra AppName Runner version: heads/main-0-g5e17bc5``
    - When ever the deploy image is used, the word "Deploy" will appear.
    - In fully containerize it would be highly irregular for the sha's to
      differ
    - In official deploy images, they should never be dirty
  '''  # noqa: E501
  if terra.settings.configured:
    if settings.terra.zone == 'controller':
      try:
        terra_version = env[f'{terra_prefix}_DEPLOY_COMMIT']
        logger.info(f"Terra {app_name} Deploy version: {terra_version}")
      except KeyError:
        try:
          terra_version = (
            Popen(
              ['git', 'describe', '--all', '--long', '--always', '--dirty'],
              cwd=env[f'{terra_prefix}_CWD'],
              stdout=PIPE,
            )
            .communicate()[0]
            .strip()
            .decode()
          )

          if not terra_version:
            raise ValueError
          logger.info(f"Terra {app_name} version: {terra_version}")
        except Exception:
          logger.warning(f"Terra {app_name} version: Unknown")
    elif settings.terra.zone == 'runner':
      try:
        terra_version = env[f'{terra_prefix}_IMAGE_COMMIT']
        logger.info(f"Terra {app_name} Runner version: {terra_version}")
      except KeyError:
        logger.warning(f"Terra {app_name} Runner version: Unknown")
  else:
    logger.warning(f"Preconfig - Terra {app_name} Runner version: Unknown")


def connect_log_terra_version(app_name, terra_prefix=None):
  '''
  Helper function to add the commit name of your app to the terra logs for your
  app.

  Parameters
  ----------
  app_name : :obj:`str`
    Your app name, used in the the log messages.
  terra_prefix : :obj:`str`, optional
    The environment variable prefix. Defaults to ``"TERRA_"+app_name.upper()``

  Example
  -------
  In your app ``__init__.py`` file, you should include the following:

  .. code-block:: python

     from terra.utils.logger import connect_log_terra_version
     connect_log_terra_version('AppName')

  See Also
  --------
  log_terra_version : Dispatch handler for this feature.
  '''

  if terra_prefix is None:
    terra_prefix = 'TERRA_' + app_name.upper()

  func = partial(log_terra_version,
                 app_name=app_name,
                 terra_prefix=terra_prefix)

  terra.core.signals.logger_configure.connect(func, weak=False)
