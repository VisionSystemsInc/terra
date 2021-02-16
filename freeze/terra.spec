# -*- mode: python ; coding: utf-8 -*-

import ast
import os
import importlib
from os import environ as env

import warnings
warnings.filterwarnings("ignore", category=ResourceWarning,
                        module='pyinstaller', message="unclosed file")

block_cipher = None

# Pyinstaller removes this, but I want it. Put it back
import sys
sys.path.insert(0, '')

app_names = ast.literal_eval(env['TERRA_APPS'])

# For each app (python import string, like "app.foo.bar"), determine the
# filename of import (prefer __main__ over __init__)
def get_app_paths(app_names):
  for name in app_names:
    # Determine the app file full path
    app = importlib.util.find_spec(name+'.__main__')
    if app is None:
      app = importlib.util.find_spec(name)
    yield app.origin

app_paths = get_app_paths(app_names)

hooks_dirs = [os.path.join(env['TERRA_CWD'], 'freeze')]

try:
  hooks_dirs.append(env['TERRA_PYINSTALLER_HOOKS_DIR'])
except KeyError:
  pass

apps_a = []
for app_path, app_name in zip(app_paths, app_names):
  extra_hidden_imports = env.get(
      f'TERRA_PYINSTALLER_{app_name.upper()}_HIDDEN_IMPORTS', [])
  if extra_hidden_imports:
    extra_hidden_imports = ast.literal_eval(extra_hidden_imports)

  apps_a.append(Analysis([app_path],
                         pathex=[env['TERRA_CWD']],
                         binaries=[],
                         datas=[],
                         hiddenimports=extra_hidden_imports,
                         # setuptools 45 - 49.0.0 needed pkg_resources.py2_warn
                         hookspath=hooks_dirs,
                         runtime_hooks=[],
                         excludes=[],
                         win_no_prefer_redirects=False,
                         win_private_assemblies=False,
                         cipher=block_cipher,
                         noarchive=False))

merge_args = []
for a, name in zip(apps_a, app_names):
  merge_args.append((a, name, name))
# This is broken until pyinstaller 4.0 is released
# https://github.com/pyinstaller/pyinstaller/pull/4303
# MERGE(*merge_args)

for a, name in zip(apps_a, app_names):
  pyz = PYZ(a.pure, a.zipped_data,
            cipher=block_cipher)
  exe = EXE(pyz,
            a.scripts,
            a.binaries,
            a.zipfiles,
            a.datas,
            a.dependencies,
            name=name,
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=False,
            console=True)
