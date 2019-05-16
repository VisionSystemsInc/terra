'''
Utilities to help write CLIs
'''
import os
import argparse


# https://gist.github.com/brantfaircloth/1252339
class FullPaths(argparse.Action):
  """
  Expand user home directory, and turns relative paths into absolute paths
  """
  def __call__(self, parser, namespace, values, option_string=None):
    setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))


# Not python3
# import copy
# class FullPathsAppend(argparse._AppendAction):
#   def __call__(self, parser, namespace, values, option_string=None):
#     items = copy.copy(argparse._ensure_value(namespace, self.dest, []))
#     items = [os.path.abspath(os.path.expanduser(item)) for item in items]
#     items.append(values)
#     setattr(namespace, self.dest, items)
