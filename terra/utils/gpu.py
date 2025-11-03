import glob
import os
import pathlib
import subprocess

from terra.logger import getLogger
logger = getLogger(__name__)


def get_load_nvidia_uvm():
  """
  Find ``<vsi_common>/linux/load_nvidia_uvm.py`` script
  """
  VSI_COMMON_DIR = os.getenv('VSI_COMMON_DIR')
  if not VSI_COMMON_DIR:
    raise IOError("Missing VSI_COMMON_DIR")

  VSI_COMMON_DIR = pathlib.Path(VSI_COMMON_DIR)
  if not VSI_COMMON_DIR.is_dir():
    raise FileNotFoundError(f"Missing directory {VSI_COMMON_DIR=}")

  load_nvidia_uvm = VSI_COMMON_DIR / 'linux' / 'load_nvidia_uvm.py'
  if not load_nvidia_uvm.is_file():
    raise FileNotFoundError(f"Missing file {load_nvidia_uvm=}")

  return load_nvidia_uvm


def gpu_check():
  '''
  Attempt to load missing GPU via ``load_nvidia_uvm.py``
  '''

  # check for nvidia cards
  if not glob.glob('/dev/nvidia[0-9]'):
    logger.debug1('No GPU cards in /dev')
    return

  # check for nvidia-uvm
  nvidia_uvm = pathlib.Path('/dev/nvidia-uvm')
  if nvidia_uvm.exists():
    logger.debug1('GPU cards found and nvidia-uvm already loaded')
    return

  # attempt to load nvidia_uvm
  load_nvidia_uvm = get_load_nvidia_uvm()
  subprocess.run(['python3', load_nvidia_uvm], shell=False, stdin=subprocess.DEVNULL)

  # check that nvidia_uvm is now loaded
  if nvidia_uvm.exists():
    logger.warning("GPU cards found and nvidia-uvm was successfully loaded")
  else:
    raise RuntimeError("GPU cards found but nvidia-uvm could not be loaded")
