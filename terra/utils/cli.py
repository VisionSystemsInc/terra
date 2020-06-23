'''
Utilities to help write CLIs
'''
import os
import argparse

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

    extra_arguments.extend(['--dbstop-if-error', debugger])

    try:
      if debugger == "pdb":
        # This doesn't exist, and will cause an ImportError
        import vsi.tools.vdb_pdb
        vsi.tools.vdb_pdb.dbstop_if_error()
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


class ArgumentParser(argparse.ArgumentParser):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.add_argument('--dbstop-if-error', nargs='?', default='pdb', type=str,
                      choices=['pdb', 'ipdb', 'rpdb', 'rpdb2'],
                      action=DbStopAction,
                      help="Automatically runs debugger's set_trace on an "
                           "unexpected exception")


def clean_path(path):
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
    setattr(namespace, self.dest, clean_path(values))


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
    # items = [clean_path(item) for item in items]
    items.append(clean_path(values))
    setattr(namespace, self.dest, items)
