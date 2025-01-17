'''
Utilities to help write CLIs
'''
import os
import argparse
import ast

from terra.core.settings import override_config


extra_arguments = list()


class DbStopAction(argparse.Action):
  # def __init__(self, option_strings, dest, nargs=None, **kwargs):
  #   if nargs is not None:
  #     raise ValueError("nargs not allowed")
  #   super().__init__(option_strings, dest, **kwargs)
  def __call__(self, parser, namespace, values, option_string=None):
    # This is a slight misuse of the "default", but I'm ok with that. Basically
    # default here means if the optional argument is not specified, since this
    # is a custom action, having a slightly different behavior here is ok.
    debugger = values or parser.get_default('dbstop_if_error')

    # TODO: Replace this with an Env var, and move the rest of the code to be
    # executed after super().parse_args. Update docker and singularity to pass
    # the env var instead
    extra_arguments.extend(['--dbstop-if-error', debugger])

    try:
      if debugger == "pdb":
        raise ImportError("pdb")
      elif debugger == "ipdb":
        import vsi.tools.vdb_ipdb
        vsi.tools.vdb_ipdb.dbstop_if_error()
      elif debugger == "rpdb":
        import vsi.tools.vdb_rpdb
        vsi.tools.vdb_rpdb.dbstop_if_error()
      elif debugger == "rpdb2":
        import vsi.tools.vdb_rpdb2
        vsi.tools.vdb_rpdb2.dbstop_if_error()
      else:
        raise ValueError(f"Unexpected debugger: {debugger}")
    except ImportError:
      import pdb
      import sys
      original_hook = sys.excepthook

      def hook(type, value, tb):
        pdb.pm()
        original_hook(type, value, tb)
      sys.excepthook = hook
    # Set a flag used by the executors, so the stack frames don't get cleared
    # during debugging
    sys.excepthook.debugger = debugger


class OverrideAction(argparse.Action):
  def __call__(self, parser, namespace, values, option_string=None):
    for setting in values:
      try:
        path, value = setting.split('=', 1)
      except ValueError as e:
        raise argparse.ArgumentError(
            self, 'There was no "=" found in setting override "--set '
            f'{setting}". If this is not a setting, remember to separate your '
            'args by adding " -- " before it. E.g. "--set foo=bar -- command '
            'args to python"') from e
      path = path.split('.')

      try:
        value = ast.literal_eval(value)
      except Exception:
        pass  # Leave it as the original string then

      entry = override_config
      for key in path[:-1]:
        if key not in entry:
          entry[key] = {}
        entry = entry[key]
      entry[path[-1]] = value


class ArgumentParser(argparse.ArgumentParser):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.add_argument('--dbstop-if-error', nargs='?', default='pdb', type=str,
                      choices=['pdb', 'ipdb', 'rpdb', 'rpdb2'],
                      action=DbStopAction,
                      help="Automatically runs debugger's set_trace on an "
                           "unexpected exception")

    self.add_argument('--set', default=[], metavar="KEY=VALUE", nargs='+',
                      help="Override terra settings, e.g. "
                           "'--set logging.level=INFO'", action=OverrideAction)

  def add_settings_file(self, default_null=False, **kwargs):
    '''
    Add positional argument for settings file
    '''

    # add_argument default kwargs
    aa_kwargs = {
      'help': 'JSON settings file',
    }

    # Let TERRA_SETTINGS_FILE (if available) be the default
    # https://stackoverflow.com/a/4480202
    TERRA_SETTINGS_FILE = os.getenv('TERRA_SETTINGS_FILE')
    if TERRA_SETTINGS_FILE:
      aa_kwargs['default'] = resolve_path(TERRA_SETTINGS_FILE)
      aa_kwargs['nargs'] = '?'
    elif default_null:
      aa_kwargs['default'] = os.devnull
      aa_kwargs['nargs'] = '?'

    # apply overrides
    aa_kwargs.update(kwargs)

    # final add argument
    self.add_argument('settings_file', type=str, action=FullPaths,
                      **aa_kwargs)


def resolve_path(path):
  # Handle lists. When nargs is used, the value is a list of strings
  if isinstance(path, list):
    return [resolve_path(x) for x in path]
  # This must be done before isabs test, or else you will get a false negative
  path = os.path.expanduser(path)

  # Support Just's changing of CWD, to keep relative paths for the user.
  if os.getenv('JUST_USER_CWD') is not None:
    # os.path.abspath, with a tweak
    path = os.fspath(path)
    if not os.path.isabs(path):
      if isinstance(path, bytes):
        cwd = os.getenvb('JUST_USER_CWD')
      else:
        cwd = os.getenv('JUST_USER_CWD')
      path = os.path.join(cwd, path)
    return os.path.normpath(path)
  return os.path.abspath(path)


# https://gist.github.com/brantfaircloth/1252339
class FullPaths(argparse.Action):
  """
  Expand user home directory, and turns relative paths into absolute paths
  """

  def __call__(self, parser, namespace, values, option_string=None):
    setattr(namespace, self.dest, resolve_path(values))


class FullPathsAppend(argparse._AppendAction):
  """
  Expand user home directory, and turns relative paths into absolute paths

  Works on multiple paths for one argument
  """

  def __call__(self, parser, namespace, values, option_string=None):
    # Python2 way
    # items = copy.copy(argparse._ensure_value(namespace, self.dest, []))
    items = getattr(namespace, self.dest, None)
    items = argparse._copy_items(items)
    # items = [resolve_path(item) for item in items]
    items.append(resolve_path(values))
    setattr(namespace, self.dest, items)
