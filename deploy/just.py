#!/usr/bin/env python

import sys
import os

if hasattr(sys, 'frozen'):
  os.environ['PATH'] = os.path.join(sys._MEIPASS, 'linux')+os.pathsep+os.environ['PATH']
  if 'VSI_COMMON_DIR' in os.environ and not \
     os.path.exists(os.path.expandvars(os.path.expanduser(os.environ['VSI_COMMON_DIR']))):
      print('ERROR: the environment variable VSI_COMMON_DIR is set to a directory that does not exist;')
      print('       please either unset or correct it')
      sys.exit(1)
  os.environ['VSI_COMMON_DIR'] = os.environ.get('VSI_COMMON_DIR', sys._MEIPASS)
  os.environ['JUST_FROZEN'] = '1'

import subprocess

if os.name=='nt':
  import pipes
  args = ' '.join([pipes.quote(x) for x in sys.argv[1:]])
  # sp=subprocess.Popen(['powershell', 'bash'], shell=False)
  sp=subprocess.Popen(['powershell', 'cmd /c color 07; bash just '+args+'; bash --rcfile "' + os.path.join(os.environ['VSI_COMMON_DIR'], '.winbashrc"')], shell=False)
  #   python -c "import pipes as p; import sys as s; print(' '.join([p.quote(x) for x in s.argv[1:]]))" "${@}"

# "cmd /c color 07; bash \"$0\" ${@}; bash --rcfile \"${VSI_COMMON_DIR}/.winbashrc\""
  sp.wait()
else:
  sp=subprocess.Popen(['just']+sys.argv[1:], shell=False)
  sp.wait()
  sys.exit(sp.returncode)