from unittest import mock
import argparse
import os
import io
import contextlib

from terra.utils.cli import (
  FullPaths, FullPathsAppend, OverrideAction,
  ArgumentParser as CliArgumentParser
)
from .utils import TestCase

from terra.core.settings import override_config


class TestSettingsFile(TestCase):
  def test_settings_file(self):
    parser = CliArgumentParser()
    parser.add_settings_file()
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
      with self.assertRaises(SystemExit):
        parser.parse_args([])
    missing_settings = ("error: the following arguments are required: "
                        "settings_file")
    self.assertIn(missing_settings, stderr.getvalue())

    parser = CliArgumentParser()
    parser.add_settings_file()
    args = parser.parse_args(["/foo"])
    self.assertEqual(args.settings_file, "/foo")

    with mock.patch.dict(os.environ, TERRA_SETTINGS_FILE='/bar'):
      parser = CliArgumentParser()
      parser.add_settings_file()
      args = parser.parse_args([])
    self.assertEqual(args.settings_file, "/bar")

    # Test default_null=True
    parser = CliArgumentParser()
    parser.add_settings_file(default_null=True)
    args = parser.parse_args([])
    self.assertEqual(args.settings_file, os.devnull)

    with mock.patch.dict(os.environ, TERRA_SETTINGS_FILE='/bar'):
      parser = CliArgumentParser()
      parser.add_settings_file(default_null=True)
      args = parser.parse_args([])
    self.assertEqual(args.settings_file, "/bar")


class TestFullPaths(TestCase):
  def test_full_paths(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('--foo', action=FullPaths)
    args = parser.parse_args(['--foo', './test.txt'])
    self.assertEqual(os.path.join(os.getcwd(), 'test.txt'), args.foo)

  def test_full_paths_append(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('--foo', action=FullPathsAppend)
    args = parser.parse_args(['--foo', './foo.txt',
                              '--foo', '/ok.txt',
                              '--foo', '~/home.txt',
                              '--foo', './bar.txt'])
    ans = [os.path.join(os.getcwd(), 'foo.txt'),
           os.path.abspath(os.path.expanduser('/ok.txt')),
           os.path.join(os.path.expanduser('~'), 'home.txt'),
           os.path.join(os.getcwd(), 'bar.txt')]
    self.assertEqual(ans, args.foo)

  @mock.patch.dict('terra.core.settings.override_config', {})
  def test_override(self, over=None):
    oa = OverrideAction(None, None)
    oa(None, None, ['foo=bar'])
    self.assertEqual(override_config, {'foo': 'bar'})

    oa(None, None, ['foo=bar1', 'a.b.c=15'])
    self.assertEqual(override_config,
                     {'foo': 'bar1',
                      'a': {'b': {'c': 15}}})

    with self.assertRaises(argparse.ArgumentError) as cm:
      oa(None, None, ['oops'])

    self.assertTrue(cm.exception.message.startswith(
        'There was no "=" found in setting '))
