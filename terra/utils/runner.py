import os

def find_file_in_path(fname, path=None):
  """
  Find a file in any of the directories on the PATH.
  Like distutils.spawn.find_executable, but works for
  any file.

  Parameters
  ----------
  fname : str
    The filename to search the PATH for.
  path : str
    An optional PATH string. If not provided, os PATH is used.


  Returns
  -------
  str
      The full path to the found file, or None if not found.
  """

  if not path:
    try:
      path = os.environ['PATH']
    except KeyError:
      return None

  for p in path.split(os.pathsep):
    possible_file_location = os.path.join(p, fname)
    if os.path.exists(possible_file_location):
      return possible_file_location

  return None
