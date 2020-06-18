# -*- mode: python ; coding: utf-8 -*-

import ast
import platform
import os
import pkgutil
import re
import importlib
from os import environ as env

block_cipher = None

# Pyinstaller removes this, but I want it. Put it back
import sys
sys.path.insert(0, '')

app_names = ast.literal_eval(env['TERRA_APPS'])

# For each app (python import string, like "app.foo.bar"), determine the
# filename of import (prefer __main__ of __init__)

def get_app_paths(app_names):
  for name in app_names:
    # # Determine base_dir, the directory responsible for the import
    # base_dir = importlib.util.find_spec(name.split('.')[0]).origin
    # base_name = os.path.split(base_dir)[-1]
    # if base_name.startswith('__init__') or base_name.startswith('__main__'):
    #   # It was a module in a package
    #   base_dir = os.path.dirname(os.path.dirname(base_dir))
    # else:
    #   # Else it must be module without a package
    #   base_dir = os.path.dirname(base_dir)

    # app_name = name

    # Determine the app file full path
    app = importlib.util.find_spec(name+'.__main__')
    if app is None:
      app = importlib.util.find_spec(name)

    # yield (app.origin, base_dir, app_name)
    yield app.origin

app_paths = get_app_paths(app_names)

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
hidden_imports = [x for x in iter_modules([env['TERRA_CWD']],
                                          exclude=['test_', '^setup'])]

try:
  hooks_dir = [env['TERRA_PYINSTALLER_HOOKS_DIR']]
except KeyError:
  hooks_dir=[]

apps_a = []
for app_path in app_paths:
  apps_a.append(Analysis([app_path],
                         pathex=[env['TERRA_CWD']],
                         binaries=[],
                         datas=[],
                         hiddenimports=['pkg_resources.py2_warn'] + hidden_imports,
                         hookspath=hooks_dir,
                         runtime_hooks=[],
                         excludes=[],
                         win_no_prefer_redirects=False,
                         win_private_assemblies=False,
                         cipher=block_cipher,
                         noarchive=False))

merge_args = []
for a, name in zip(apps_a, app_names):
  merge_args.append((a, name, name))
MERGE(*merge_args)

for a, name in zip(apps_a, app_names):
  pyz = PYZ(a.pure, a.zipped_data,
            cipher=block_cipher)
  exe = EXE(pyz,
            a.scripts,
            [],
            exclude_binaries=True,
            name=name,
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            console=True)
  coll = COLLECT(exe,
                 a.binaries,
                 a.zipfiles,
                 a.datas,
                 strip=False,
                 upx=True,
                 upx_exclude=[],
                 name=name)
