from unittest import mock
import pathlib
import os
import ntpath
import posixpath

from .utils import TestCase
# from .test_compute_utils import TestComputeUtilsCase
import terra.utils.path as utils


class TestTranslateUtils(TestCase):
  def _nt_or_posix(self, nt_obj, posix_obj, platform):
    return nt_obj if platform in ('windows', 'nt') else posix_obj

  def _drive(self, host_platform, container_platform):
    return (self._nt_or_posix('H:\\', '/', host_platform),
            self._nt_or_posix('C:\\', '/', container_platform))

  def _os(self, host_platform, container_platform):
    return (self._nt_or_posix(ntpath, posixpath, host_platform),
            self._nt_or_posix(ntpath, posixpath, container_platform))

  def _create_volume_map(self, host_platform, container_platform):

    # test data
    test_data = [
        (('src', 'abc'), ('dst', 'ABC')),
        (('src', 'abc_output'), ('dst', 'OUTPUT')),
        (('src', 'def'), ('dst', 'DEF')),
        (('src', 'abc.json'), ('dst', 'ABC.json')),
    ]

    # append "drive" to test data
    host_drv, container_drv = self._drive(host_platform, container_platform)
    test_data = [((host_drv, *src), (container_drv, *dst))
                 for src, dst in test_data]

    # volume map
    host_os, container_os = self._os(host_platform, container_platform)
    volume_map = [(host_os.join(*src), container_os.join(*dst))
                  for src, dst in test_data]
    return volume_map

  def _test_pathlib_map(self, container_platform):
    host_obj_type = type(pathlib.Path())
    container_obj_type = self._nt_or_posix(pathlib.PureWindowsPath,
                                           pathlib.PurePosixPath,
                                           container_platform)

    volume_map = self._create_volume_map(os.name, container_platform)
    pathlib_map = utils.pathlib_map(volume_map, container_platform)

    for host_obj, container_obj in pathlib_map:
      self.assertIsInstance(host_obj, host_obj_type)
      self.assertIsInstance(container_obj, container_obj_type)

  def test_pathlib_map_linux(self):
    self._test_pathlib_map('linux')

  def test_pathlib_map_windows(self):
    self._test_pathlib_map('windows')

  def _test_patch_volume(self, container_platform):
    volume_map = self._create_volume_map(os.name, container_platform)
    host_os, container_os = self._os(os.name, container_platform)

    for host_vol, container_vol in volume_map:
      is_file = '.' in pathlib.Path(host_vol).parts[-1]
      if is_file:
        # direct file mapping only
        test_items = [[]]
      else:
        # this directory, subdirectory, and file mappings
        test_items = [[], ['xyz'], ['xyz', 'xyz']]
        test_items += [[*ti, 'file.json'] for ti in test_items]

      for item in test_items:
        host_item = host_os.join(host_vol, *item)
        container_item = container_os.join(container_vol, *item)
        result = utils.patch_volume(host_item, volume_map, container_platform)
        self.assertEqual(result, container_item)

  def test_patch_volume_linux(self):
    self._test_patch_volume('linux')

  def test_patch_volume_windows(self):
    self._test_patch_volume('windows')

  @mock.patch.dict(os.environ, FOO='/foo/bar', BAR='bar')
  def test_patch_volume_expand(self):
    # Test variable expansion and user home dir expansion
    volume_map = [('/foo/bar', '/dst')]
    self.assertEqual(utils.patch_volume('${FOO}/baz', volume_map, 'linux'),
                     '/dst/baz')
    self.assertEqual(utils.patch_volume('/foo/${BAR}/car',
                                        volume_map,
                                        'linux'),
                     '/dst/car')
    volume_map = [(os.path.expanduser('~'), '/myhome')]
    self.assertEqual(utils.patch_volume('~/${BAR}/car', volume_map, 'linux'),
                     '/myhome/bar/car')

# No test for translate_settings_paths?