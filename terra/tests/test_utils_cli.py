import argparse
import os

from terra.utils.cli import FullPaths, FullPathsAppend
from .utils import TestCase


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
           os.path.expanduser('/ok.txt'),
           os.path.join(os.path.expanduser('~'), 'home.txt'),
           os.path.join(os.getcwd(), 'bar.txt')]
    self.assertEqual(ans, args.foo)
