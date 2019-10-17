import os
from os import environ as env
from shlex import quote
from subprocess import Popen
import distutils.spawn

from vsi.tools.diff import dict_diff

import terra.compute.utils
from terra.compute.base import BaseCompute
from terra.logger import getLogger, DEBUG1
logger = getLogger(__name__)


# Not called Compute, because this is not meant to be an actual compute, but a
# parent class.
class JustCompute(BaseCompute):
  '''
  TODO: Remove this, it doesn't need to be a class
  '''
  def just(self, *args, **kwargs):
    '''
    Run a ``just`` command. Primarily used to run ``--wrap``

    Arguments
    ---------
    justfile : :class:`str`, optional
        Optionally allow you to specify a custom ``Justfile``. Defaults to
        Terra's ``Justfile`` is used, which is the correct course of action
        most of the time
    env : :class:`dict`, optional
        Sets environment variables. Same as Popen's ``env``, except
        ``JUSTFILE`` is programatically set, and cannot be overridden any other
        way than chaning the ``justfile`` variable
    *args :
        List of arguments to be pass to ``just``
    **kwargs :
        Arguments sent to ``Popen`` command
    '''

    logger.debug('Running: ' + ' '.join(
        [quote(x) for x in ('just',) + args]))

    just_env = kwargs.pop('env', env).copy()
    justfile = kwargs.pop(
        'justfile', os.path.join(env['TERRA_TERRA_DIR'], 'Justfile'))
    just_env['JUSTFILE'] = justfile

    if logger.getEffectiveLevel() <= DEBUG1:
      dd = dict_diff(env, just_env)[3]
      if dd:
        logger.debug1('Environment Modification:\n' + '\n'.join(dd))

    # Get bash path for windows compatibility. I can't explain this error, but
    # while the PATH is set right, I can't call "bash" because the WSL bash is
    # called instead. It appears to be a bug in the windows kernel as
    # subprocess._winapi.CreateProcess('bash', 'bash --version', None, None,
    # 0, 0, os.environ, None, None) even fails.
    # Microsoft probably has a special exception for the word "bash" that
    # calls WSL bash on execute :(
    kwargs['executable'] = distutils.spawn.find_executable('bash')
    # Have to call bash for windows compatibility, no shebang support
    pid = Popen(('bash', 'just') + args, env=just_env, **kwargs)
    return pid
