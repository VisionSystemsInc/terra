import re
import pkgutil
import os
from os import environ as env

# Discover all modules in a package, to help hidden imports
def iter_modules(path=None, prefix='', exclude=[]):
  exclude = [ex if isinstance(ex, re.Pattern) else re.compile(ex)
             for ex in exclude]
  for pkg in pkgutil.iter_modules(path, prefix):
    if any((ex.search(pkg.name) for ex in exclude)):
      continue
    yield pkg.name
    if pkg.ispkg:
      yield from iter_modules([os.path.join(pkg.module_finder.path,
                                            pkg.name.split('.')[-1])],
                              pkg.name+'.', exclude)

# Include all of terra, many parts of terra use hidden imports
hiddenimports = [x for x in iter_modules([env['TERRA_CWD']],
                                         exclude=['test_', '^setup'])]