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

# just_files=[(os.path.join(env['VSI_COMMON_DIR'], 'linux'), 'linux'),
#             (os.path.join(env['VSI_COMMON_DIR'], 'env.bsh'), '.'),
#             (os.path.join(env['VSI_COMMON_DIR'], 'Justfile'), '.')]
# # Add for recipes
# just_files.append((os.path.join(env['VSI_COMMON_DIR'], 'docker'), 'docker'))
# # Add tests to test just executable
# # just_files.append(('./vsi_common/tests', 'tests'))

importlib.util.find_spec('dsm')

apps = ast.literal_eval(env['TERRA_APPS'])
def get_app_paths(apps):
  for app in apps:
    app = importlib.util.find_spec(app+'.__main__')
    if app:
      yield app.origin
    else:
      yield importlib.util.find_spec(app).origin
apps = list(get_app_paths(apps))


if platform.system() == 'Windows':
  console=False
  # console=True
else:
  console=True

# if env.get('VSI_MUSL', None)=='1':
#   name='juste-'+platform.system()+'-musl-x86_64'
# else:
#   name='juste-'+platform.system()+'-x86_64'

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

hidden_imports = [x for x in iter_modules([env['TERRA_CWD']],
                                          exclude=['test_', '^setup'])]



for app in apps:
  hidden_imports += [x for x in iter_modules(
      # This is a hack \|/
      [os.path.dirname(os.path.dirname(app))],
      exclude=['test_', '^setup'])]

# apps.append(os.path.join(env['TERRA_CWD'], 'deploy', 'just.py'))
# apps = [os.path.join(env['TERRA_CWD'], 'deploy', 'just.py')] + apps

app_a = Analysis(apps,
                 pathex=[env['TERRA_CWD']],
                 binaries=[],
                 datas=[],
                 hiddenimports=['pkg_resources.py2_warn'] + hidden_imports,
                 hookspath=[],
                 runtime_hooks=[],
                 excludes=[],
                 win_no_prefer_redirects=False,
                 win_private_assemblies=False,
                 cipher=block_cipher,
                 noarchive=False)

pyz = PYZ(app_a.pure, app_a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          app_a.scripts,
          [],
          exclude_binaries=True,
          name='dsm',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=console)
coll = COLLECT(exe,
               app_a.binaries,
               app_a.zipfiles,
               app_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='terra')

# just_a = Analysis([os.path.join(env['TERRA_CWD'], 'deploy', 'just.py')],
#                   pathex=[],
#                   binaries=[],
#                   datas=just_files,
#                   hookspath=[],
#                   runtime_hooks=[],
#                   excludes=[],
#                   win_no_prefer_redirects=False,
#                   win_private_assemblies=False,
#                   cipher=block_cipher,
#                   noarchive=False)
# just_pyz = PYZ(just_a.pure, just_a.zipped_data,
#                cipher=block_cipher)
# just_exe = EXE(just_pyz,
#                just_a.scripts,
#                [],
#                exclude_binaries=True,
#                name='just',
#                debug=False,
#                bootloader_ignore_signals=False,
#                strip=False,
#                upx=True,
#                console=console)
# just_coll = COLLECT(just_exe,
#                     just_a.binaries,
#                     just_a.zipfiles,
#                     just_a.datas,
#                     strip=False,
#                     upx=True,
#                     upx_exclude=[],
#                     name='just')

# MERGE((app_a, 'dsm', 'dsm'), (just_a, 'just', 'just'))
