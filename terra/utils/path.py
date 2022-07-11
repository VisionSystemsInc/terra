import pathlib
import os

from vsi.tools.python import nested_patch

from terra import settings
from terra.core.settings import filename_suffixes, TerraJSONEncoder
from terra.logger import getLogger
logger = getLogger(__name__)

'''
Terra has multiple zones, the "controller", the "compute", the "executor", and
in the case of celery, the "task_controller" zone. Each zone has the potential
to have the same files represented by different paths; e.g. volume binds in
containers.

These utilities will help with handling those path translations.
'''

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


def reverse_volume_map(volume_map):
  reverse_map = [[x[1], x[0]] for x in volume_map]
  reverse_map.reverse()
  return reverse_map


def translate_paths_chain(payload, *maps):
  if any(maps):
    # If either translation is needed, start by applying the ~ home dir
    # expansion and settings_property (which wouldn't have made it through
    # pure json conversion, but the ~ will)
    payload = TerraJSONEncoder.serializableSettings(payload)
    # Go from compute runner to master controller
    for volume_map in maps:
      if volume_map:
        payload = translate_settings_paths(payload, volume_map)
  return payload


def resolve_path(path):
  path = os.path.normpath(os.path.expanduser(os.path.expandvars(path)))
  if settings.terra.zone == 'controller':
    return path
  else:
    if settings.compute.volume_map:
      path = patch_volume(path, settings.compute.volume_map)

    if settings.terra.zone == 'task' and settings.executor.volume_map:
      path = patch_volume(path, settings.executor.volume_map)

    return path