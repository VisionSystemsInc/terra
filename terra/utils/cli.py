'''
Utilities to help write CLIs
'''
import os
import argparse

def clean_path(path):
  return os.path.abspath(os.path.expanduser(path))


# https://gist.github.com/brantfaircloth/1252339
class FullPaths(argparse.Action):
  """
  Expand user home directory, and turns relative paths into absolute paths
  """

  def __call__(self, parser, namespace, values, option_string=None):
    setattr(namespace, self.dest, clean_path(values))


class FullPathsAppend(argparse._AppendAction):
  def __call__(self, parser, namespace, values, option_string=None):
    # Python2 way
    # items = copy.copy(argparse._ensure_value(namespace, self.dest, []))
    items = getattr(namespace, self.dest, None)
    items = argparse._copy_items(items)
    # items = [clean_path(item) for item in items]
    items.append(clean_path(values))
    setattr(namespace, self.dest, items)
