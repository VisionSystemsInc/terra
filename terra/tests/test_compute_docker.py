import os
import re
from unittest import mock

from terra import settings
from terra.compute import base
from terra.compute import docker

from .utils import TestCase


patches = []


def setUpModule():
  patches.append(mock.patch.object(settings, '_wrapped', None))
  # patches.append(mock.patch.dict(base.services, clear=True))
  for patch in patches:
    patch.start()
  settings.configure({'compute': {'arch': 'docker'}})


def tearDownModule():
  for patch in patches:
    patch.stop()


class TestDockerRe(TestCase):
  def test_re(self):
    # Copied from test-docker_functions.bsh "Docker volume string parsing"
    host_paths = (".",
                  "/",
                  "C:\\",
                  "/foo/bar",
                  "/foo/b  ar",
                  "D:/foo/bar",
                  "D:\\foo\\bar",
                  "vl")
    docker_paths = ("/test/this",
                    "/te st/th  is",
                    "C:\\",
                    "z")
    test_volume_flags = ("",
                         ":ro",
                         ":ro:z",
                         ":z:ro",
                         ":Z:rshared:rw:nocopy")

    parser = re.compile(docker.docker_volume_re)

    for host_path in host_paths:
      for docker_path in docker_paths:
        for test_volume_flag in test_volume_flags:
          results = parser.match(host_path + ":" + docker_path +
                                 test_volume_flag).groups()

          self.assertEqual(results[0], host_path)
          self.assertEqual(results[2], docker_path)
          self.assertEqual(results[4], test_volume_flag)


###############################################################################


def mock_popen(*args, **kwargs):
  return (args, kwargs, os.environ.copy())


class TestDockerJust(TestCase):
  @mock.patch.object(docker, 'Popen', mock_popen)
  def test_just(self):
    original_env = os.environ.copy()

    default_justfile = os.path.join(os.environ['TERRA_TERRA_DIR'], 'Justfile')
    compute = docker.Compute()
    args, kwargs, env = compute.just("foo  bar")
    self.assertEqual(args, (('just', 'foo  bar'),))
    self.assertEqual(kwargs, {})
    self.assertEqual(env['JUSTFILE'], default_justfile)

    # Custom env
    args, kwargs, env = compute.just("foo", "bar", add_env={"FOO": "BAR"})
    self.assertEqual(args, (('just', 'foo', 'bar'),))
    self.assertEqual(kwargs, {})
    self.assertEqual(env['FOO'], 'BAR')
    self.assertEqual(env['JUSTFILE'], default_justfile)

    # test custom justfile
    args, kwargs, env = compute.just("foobar", justfile="/foo/bar")
    self.assertEqual(args, (('just', 'foobar'),))
    self.assertEqual(kwargs, {})
    self.assertEqual(env['JUSTFILE'], "/foo/bar")

    # test kwargs
    args, kwargs, env = compute.just("foobar", shell=False)
    self.assertEqual(args, (('just', 'foobar'),))
    self.assertEqual(kwargs, {'shell':False})
    self.assertEqual(env['JUSTFILE'], default_justfile)

    # Test logging code
    with self.assertLogs(docker.__name__, level="DEBUG1") as cm:
      env = os.environ.copy()
      env.pop('PATH')
      compute.just("foo", "bar", env=env, add_env={"FOO": "BAR"})

    env_lines = [x for x in cm.output if "Environment Modification:" in x][0]
    env_lines = env_lines.split('\n')
    self.assertEqual(len(env_lines), 4)

    self.assertTrue(any(o.startswith('- PATH:') for o in env_lines))
    self.assertTrue(any(o.startswith('+ FOO:') for o in env_lines))
    self.assertTrue(any(o.startswith('+ JUSTFILE:') for o in env_lines))

    # Make sure nothing inadvertently changed environ
    self.assertEqual(original_env, os.environ)

###############################################################################

def mock_just(return_value):
  def just(self, *args, **kwargs):
    just.args = args
    just.kwargs = kwargs
    return type('blah', (object,), {'wait': lambda self: return_value})()
  return just

class MockJustService:
  compose_file = "file1"
  compose_service_name = "launch"
  command = ["ls"]
  env = {"BAR": "FOO"}

class TestDockerRun(TestCase):
  @mock.patch.object(docker.Compute, 'just', mock_just(0))
  def test_run(self):
    compute = docker.Compute()
    compute.run(MockJustService())

    # This test looks fragile
    self.assertEqual(docker.Compute.just.args, ('--wrap',
        'Just-docker-compose', '-f', 'file1', 'run', 'launch', 'ls'))
    self.assertEqual(docker.Compute.just.kwargs, {'add_env': {'BAR': 'FOO'}})

  @mock.patch.object(docker.Compute, 'just', mock_just(1))
  def test_failed_run(self):
    compute = docker.Compute()
    with self.assertRaises(base.ServiceRunFailed):
      compute.run(MockJustService())


###############################################################################


class TestDockerConfig(TestCase):
  def setUp(self):
    self.patch = mock.patch.object(docker.Compute, 'just',
                                   self.mock_just_config)
    self.patch.start()

  def tearDown(self):
    self.patch.stop()

  # Create a special mock functions that takes the Tests self as _self, and the
  # rest of the args as args/kwargs. This lets me do testing inside the mocked
  # function.
  def mock_just_config(_self, *args, **kwargs):
    _self.assertEqual(args, _self.expected_args)
    _self.assertEqual(kwargs, _self.expected_kwargs)
    return type('blah', (object,),
                {'communicate': lambda self: ('out', None)})()

  def test_config(self):
    expected_args1 = ('--wrap', 'Just-docker-compose', '-f', 'file1')
    expected_args2 = ('config',)
    compute = docker.Compute()

    self.expected_args = expected_args1 + expected_args2
    self.expected_kwargs = {'stdout': docker.PIPE, 'env': {'BAR':'FOO'}}
    self.assertEqual(compute.config(MockJustService()), 'out')

    self.expected_args = (expected_args1 +
                          ('-f', 'file15.yml', '-f', 'file2.yaml') +
                          expected_args2)
    self.assertEqual(compute.configService(MockJustService(),
                                           ['file15.yml', 'file2.yaml']),
                     'out')




###############################################################################


def mock_config():
  pass


class TestDockerMap(TestCase):
  pass
