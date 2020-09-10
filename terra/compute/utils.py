# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be
#        used to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from importlib import import_module
import os
from os import environ as env
from shlex import quote
from subprocess import Popen
import distutils.spawn
import pathlib

from vsi.tools.diff import dict_diff
from vsi.tools.python import nested_patch

from terra.core.utils import Handler
import terra.core.signals
from terra import settings
import terra.compute.base
from terra.core.settings import filename_suffixes
from terra.logger import getLogger, DEBUG1
logger = getLogger(__name__)


class ComputeHandler(Handler):
  '''
  The :class:`ComputeHandler` class gives a single entrypoint to interact with
  the compute architecture, no matter what arch type it is. A standard way to
  call ``run``, etc...
  '''

  def _connect_backend(self):
    '''
    Loads the compute's backend's base module, given either a fully qualified
    compute backend name, or a partial (``terra.compute.{partial}``), and
    then returns a connection to the backend

    A Backend should have two classes defined:

    * ``Compute`` based off of :class:`terra.compute.base.BaseCompute`
    * ``Service`` based off of :class:`terra.compute.base.BaseService`

    Parameters
    ----------
    self._override_type : :class:`str`, optional
        If not ``None``, override the name of the backend to load.
    '''

    backend_name = self._override_type

    if backend_name is None:
      backend_name = settings.compute.arch

    try:
      module = import_module(f'{backend_name}')
      if not hasattr(module, 'Compute'):
        raise ImportError(f"module '{backend_name}' has no attribute "
                          "'Compute'")
    except ImportError:
      module = import_module(f'terra.compute.{backend_name}')

    return module.Compute()


compute = ComputeHandler()
'''ComputeHandler: The compute handler that all apps will be interfacing with.
For the most part, workflows will be interacting with :data:`compute` to
``run`` services. Easier access via ``terra.compute.compute``
'''
terra.core.signals.logger_configure.connect(
    lambda *args, **kwargs: compute.configure_logger(*args, **kwargs),
    weak=False)
terra.core.signals.logger_reconfigure.connect(
    lambda *args, **kwargs: compute.reconfigure_logger(*args, **kwargs),
    weak=False)


def get_default_service_class(cls):
  '''
  Gets a compute class' default Service class from the class object.

  Since computes are named ``Compute`` in the base module, the class
  ``Service`` should be defined in the same file. This will return that
  ``Service`` class

  Arguments
  ---------
  cls : type
      The compute class whose service class you want
  '''
  module = import_module(f'{cls.__module__}')
  return module.Service


def load_service(name_or_class):
  '''
  Get (and optionally import) a service by name. Also accepts the class itself
  or an instance of a class.

  Parameters
  ----------
  name_or_class : :class:`str` or :term:`class` or instance
      The service being loaded

  Returns
  -------
  object
      Instead of the class specified. If ``name_or_class`` was already an
      instance, the same instance is returned
  '''

  if not isinstance(name_or_class, str):
    # If already instance, return it
    if not isinstance(name_or_class, type):
      return name_or_class
    # TODO: Not really designed for nested classes, so don't use __qualname__
    name_or_class = f'{name_or_class.__module__}.{name_or_class.__name__}'
  else:
    module = name_or_class.rsplit('.', 1)[0]
    # Import to trigger registration. Don't need return value
    import_module(module)

  try:
    services = terra.compute.base.services[name_or_class]
  except KeyError:
    logger.fatal(f'{name_or_class} is not registered')
    raise

  cls = type(compute._connection)

  if cls not in services:
    logger.info(f'Using default {cls} compute handler for {name_or_class}')
    return get_default_service_class(cls)()

  return services[cls]()


# The rest is not part of the Django License


def just(*args, **kwargs):
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
  justfile = kwargs.pop('justfile', None)
  if not justfile:
    justfile = os.path.join(env['TERRA_TERRA_DIR'], 'Justfile')
  just_env['JUSTFILE'] = justfile

  if logger.getEffectiveLevel() <= DEBUG1:
    dd = dict_diff(env, just_env)[3]
    if dd:
      logger.debug4('Environment Modification:\n' + '\n'.join(dd))

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


def pathlib_map(volume_map, container_platform='linux'):
  '''
  Translate volume mapping from strings to pathlib objects. Source paths on
  the host system are instantiated as :ref:`concrete-paths` allowing use of
  the :meth:`pathlib.Path.resolve` function.  Paths in the container are
  instantiated as :ref:`pure-paths` of the appropriate type.

  Parameters
  ----------
  volume_map : :obj:`list` of :obj:`tuple` of :obj:`str`
    List of tuples. Each tuple contains two strings of the form
    ``(host_str, container_str)``.
  container_platform : :obj:`str`, optional
    String specifying container platform, ``linux`` or ``windows``.
    Defaults to ``linux``

  Returns
  ----------
  :obj:`list` of :obj:`tuple` of :obj:`pathlib` objects
    List of tuples. Each tuple contains two pathlib objects of the form
    ``(host_pathlib, container_pathlib)``. ``host_pathlib`` objects are
    :ref:`concrete-paths` suitable for the current host OS.
    ``container_pathlib`` objects are :ref:`pure-paths` suitable
    for the specified ``container_platform``.

  '''
  pure_path = (pathlib.PureWindowsPath if container_platform == 'windows'
               else pathlib.PurePosixPath)

  return [(pathlib.Path(host_str).resolve(), pure_path(container_str))
          for host_str, container_str in volume_map]


def patch_volume(value, volume_map, container_platform='linux'):
  '''
  Translate path value according to volume_map.

  Parameters
  ----------
  value : :obj:`str`
    Path value on the host
  volume_map : :obj:`list` of :obj:`tuple` of :obj:`str`
    List of tuples. Each tuple contains two strings of the form
    ``(host_str, container_str)``.
  container_platform : :obj:`str`, optional
    String specifying container platform, ``linux`` or ``windows``.
    Defaults to ``linux``.

  Returns
  ----------
  :obj:`str`
    Translated path value in the container. If translation is not possible,
    function returns the original value.

  '''
  if isinstance(value, str):
    # If we don't expand before resolve, then both ${FOO} and ~/foo are treated
    # as relative paths, and the PWD is prepended. Further, without proper
    # expansion, the correct translations can't be made, so the variables need
    # to be expanded here, and no later.
    value_pathlib = pathlib.Path(os.path.expandvars(value))
    value_pathlib = value_pathlib.expanduser().resolve()
    volume_map_pathlib = pathlib_map(volume_map, container_platform)

    for host_pathlib, container_pathlib in volume_map_pathlib:
      try:
        remainder = value_pathlib.relative_to(host_pathlib)
      except ValueError:
        continue
      return str(container_pathlib / remainder)

  return value


def translate_settings_paths(container_config, volume_map,
                             container_platform='linux'):

  if os.name == "nt":  # pragma: no linux cover
    logger.warning("Windows volume mapping is experimental.")

  # Apply map translation to settings configuration
  return nested_patch(
      container_config,
      lambda key, value: (isinstance(key, str)
                          and any(key.endswith(pattern)
                                  for pattern in filename_suffixes)),
      lambda key, value: patch_volume(value, reversed(volume_map))
  )
