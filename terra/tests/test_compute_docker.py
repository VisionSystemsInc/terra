import os
import re
from unittest import mock
import warnings

from terra import settings
from terra.compute import base
from terra.compute import docker
from terra.compute import compute
from terra.core.utils import cached_property

from .utils import TestCase


patches = []


def setUpModule():
  patches.append(mock.patch.object(settings, '_wrapped', None))
  # This resets the _connection to an called state
  # patches.append(mock.patch.dict(compute.__dict__, '_connection', cached_property(lambda self: self._connect_backend())))

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
  # Create a special mock functions that takes the Tests self as _self, and the
  # rest of the args as args/kwargs. This lets me do testing inside the mocked
  # function. self.expected_args and self.expected_kwargs should be set by the
  # test function before calling. self.return_value should also be set before
  # calling, so that the expected return value is returned
  def mock_just(_self, *args, **kwargs):
    _self.assertEqual(_self.expected_args, args)
    _self.assertEqual(_self.expected_kwargs, kwargs)
    return type('blah', (object,), {'wait': lambda self: _self.return_value})()

  def setUp(self):
    self.patch = mock.patch.object(docker.Compute, 'just', self.mock_just)
    self.patch.start()

  def tearDown(self):
    self.patch.stop()

  def test_run(self):
    compute = docker.Compute()

    self.return_value = 0
    # This part of the test looks fragile
    self.expected_args = ('--wrap', 'Just-docker-compose', '-f', 'file1', 'run', 'launch', 'ls')
    self.expected_kwargs = {'add_env': {'BAR': 'FOO'}}
    compute.run(MockJustService())

    # Test a non-zero return value
    self.return_value = 1
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

mock_yaml = r'''secrets:
  redis_commander_secret:
    file: /opt/projects/terra/terra_dsm/external/terra/redis_commander_password.secret
  redis_secret:
    file: /opt/projects/terra/terra_dsm/external/terra/redis_password.secret
services:
  ipykernel:
    build:
      args:
        TERRA_PIPEVN_DEV: '0'
      context: /opt/projects/terra/terra_dsm/external/terra
      dockerfile: docker/terra.Dockerfile
    cap_add:
    - SYS_PTRACE
    environment:
      DISPLAY: :1
      DOCKER_GIDS: 1000 10 974
      DOCKER_GROUP_NAMES: group wheel docker
      DOCKER_UID: '1001'
      DOCKER_USERNAME: user
      JUSTFILE: /terra/docker/terra.Justfile
      JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES: /venv
      JUST_SETTINGS: /terra/terra.env
      PYTHONPATH: /src
      TERRA_APP_DIR: /src
      TERRA_APP_DIR_HOST: /opt/projects/terra/terra_dsm/external/terra
      TERRA_REDIS_COMMANDER_PORT: '4567'
      TERRA_REDIS_COMMANDER_PORT_HOST: '4567'
      TERRA_REDIS_DIR: /data
      TERRA_REDIS_DIR_HOST: terra-redis
      TERRA_REDIS_HOSTNAME: terra-redis
      TERRA_REDIS_HOSTNAME_HOST: localhost
      TERRA_REDIS_PORT: '6379'
      TERRA_REDIS_PORT_HOST: '6379'
      TERRA_REDIS_SECRET: redis_password
      TERRA_REDIS_SECRET_HOST: redis_secret
      TERRA_SETTINGS_DIR: /settings
      TERRA_TERRA_DIR: /terra
      TERRA_TERRA_DIR_HOST: /opt/projects/terra/terra_dsm/external/terra
      TZ: /usr/share/zoneinfo/America/New_York]
    image: terra:terra_me
    ports:
    - published: 10001
      target: 10001
    - published: 10002
      target: 10002
    - published: 10003
      target: 10003
    - published: 10004
      target: 10004
    - published: 10005
      target: 10005
    volumes:
    - /tmp:/bar:ro
    - read_only: true
      source: /opt/projects/terra/terra_dsm/external/terra
      target: /src
      type: bind
    - read_only: true
      source: /opt/projects/terra/terra_dsm/external/terra
      target: /terra
      type: bind
    - /tmp/.X11-unix:/tmp/.X11-unix:ro
    - source: terra-venv
      target: /venv
      type: volume
    - read_only: true
      source: /opt/projects/terra/terra_dsm/external/terra/external/vsi_common
      target: /vsi
      type: bind
  redis-commander:
    command: "sh -c '\n  echo -n '\"'\"'{\n    \"connections\":[\n      {\n      \
      \  \"password\": \"'\"'\"' > /redis-commander/config/local-production.json\n\
      \  cat /run/secrets/redis_password | sed '\"'\"'s|\\\\|\\\\\\\\|g;s|\"|\\\\\"\
      |g'\"'\"' >> /redis-commander/config/local-production.json\n  echo -n '\"'\"\
      '\",\n        \"host\": \"terra-redis\",\n        \"label\": \"terra\",\n  \
      \      \"dbIndex\": 0,\n        \"connectionName\": \"redis-commander\",\n \
      \       \"port\": \"6379\"\n      }\n    ],\n    \"server\": {\n      \"address\"\
      : \"0.0.0.0\",\n      \"port\": 4567,\n      \"httpAuth\": {\n        \"username\"\
      : \"admin\",\n        \"passwordHash\": \"'\"'\"'>> /redis-commander/config/local-production.json\n\
      \    cat \"/run/secrets/redis_commander_password.secret\" | sed '\"'\"'s|\\\\\
      |\\\\\\\\|g;s|\"|\\\\\"|g'\"'\"' >> /redis-commander/config/local-production.json\n\
      \    echo '\"'\"'\"\n      }\n    }\n  }'\"'\"' >> /redis-commander/config/local-production.json\n\
      \  /redis-commander/docker/entrypoint.sh'\n"
    environment:
      TERRA_APP_DIR: /src
      TERRA_APP_DIR_HOST: /opt/projects/terra/terra_dsm/external/terra
      TERRA_REDIS_COMMANDER_PORT: '4567'
      TERRA_REDIS_COMMANDER_PORT_HOST: '4567'
      TERRA_REDIS_DIR: /data
      TERRA_REDIS_DIR_HOST: terra-redis
      TERRA_REDIS_HOSTNAME: terra-redis
      TERRA_REDIS_HOSTNAME_HOST: localhost
      TERRA_REDIS_PORT: '6379'
      TERRA_REDIS_PORT_HOST: '6379'
      TERRA_REDIS_SECRET: redis_password
      TERRA_REDIS_SECRET_HOST: redis_secret
      TERRA_SETTINGS_DIR: /settings
      TERRA_TERRA_DIR: /terra
      TERRA_TERRA_DIR_HOST: /opt/projects/terra/terra_dsm/external/terra
    image: rediscommander/redis-commander
    ports:
    - published: 4567
      target: 4567
    secrets:
    - source: redis_commander_secret
      target: redis_commander_password.secret
    - source: redis_secret
      target: redis_password
    volumes:
    - /tmp:/bar:ro
    - /tmp/.X11-unix:/tmp/.X11-unix:ro
  terra:
    build:
      args:
        TERRA_PIPEVN_DEV: '0'
      context: /opt/projects/terra/terra_dsm/external/terra
      dockerfile: docker/terra.Dockerfile
    cap_add:
    - SYS_PTRACE
    environment:
      DISPLAY: :1
      DOCKER_GIDS: 1000 10 974
      DOCKER_GROUP_NAMES: group wheel docker
      DOCKER_UID: '1001'
      DOCKER_USERNAME: user
      JUSTFILE: /terra/docker/terra.Justfile
      JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES: /venv
      JUST_SETTINGS: /terra/terra.env
      PYTHONPATH: /src
      TERRA_APP_DIR: /src
      TERRA_APP_DIR_HOST: /opt/projects/terra/terra_dsm/external/terra
      TERRA_REDIS_COMMANDER_PORT: '4567'
      TERRA_REDIS_COMMANDER_PORT_HOST: '4567'
      TERRA_REDIS_DIR: /data
      TERRA_REDIS_DIR_HOST: terra-redis
      TERRA_REDIS_HOSTNAME: terra-redis
      TERRA_REDIS_HOSTNAME_HOST: localhost
      TERRA_REDIS_PORT: '6379'
      TERRA_REDIS_PORT_HOST: '6379'
      TERRA_REDIS_SECRET: redis_password
      TERRA_REDIS_SECRET_HOST: redis_secret
      TERRA_SETTINGS_DIR: /settings
      TERRA_TERRA_DIR: /terra
      TERRA_TERRA_DIR_HOST: /opt/projects/terra/terra_dsm/external/terra
      TZ: /usr/share/zoneinfo/America/New_York]
    image: terra:terra_me
    volumes:
    - /tmp:/bar:ro
    - read_only: true
      source: /opt/projects/terra/terra_dsm/external/terra
      target: /src
      type: bind
    - read_only: true
      source: /opt/projects/terra/terra_dsm/external/terra
      target: /terra
      type: bind
    - /tmp/.X11-unix:/tmp/.X11-unix:ro
    - source: terra-venv
      target: /venv
      type: volume
    - read_only: true
      source: /opt/projects/terra/terra_dsm/external/terra/external/vsi_common
      target: /vsi
      type: bind
  test:
    build:
      args:
        TERRA_PIPEVN_DEV: '0'
      context: /opt/projects/terra/terra_dsm/external/terra
      dockerfile: docker/terra.Dockerfile
    cap_add:
    - SYS_PTRACE
    environment:
      DISPLAY: :1
      DOCKER_GIDS: 1000 10 974
      DOCKER_GROUP_NAMES: group wheel docker
      DOCKER_UID: '1001'
      DOCKER_USERNAME: user
      JUSTFILE: /terra/docker/terra.Justfile
      JUST_DOCKER_ENTRYPOINT_INTERNAL_VOLUMES: /venv
      JUST_SETTINGS: /terra/terra.env
      PYTHONPATH: /src
      TERRA_APP_DIR: /src
      TERRA_APP_DIR_HOST: /opt/projects/terra/terra_dsm/external/terra
      TERRA_REDIS_COMMANDER_PORT: '4567'
      TERRA_REDIS_COMMANDER_PORT_HOST: '4567'
      TERRA_REDIS_DIR: /data
      TERRA_REDIS_DIR_HOST: terra-redis
      TERRA_REDIS_HOSTNAME: terra-redis
      TERRA_REDIS_HOSTNAME_HOST: localhost
      TERRA_REDIS_PORT: '6379'
      TERRA_REDIS_PORT_HOST: '6379'
      TERRA_REDIS_SECRET: redis_password
      TERRA_REDIS_SECRET_HOST: redis_secret
      TERRA_SETTINGS_DIR: /settings
      TERRA_TERRA_DIR: /terra
      TERRA_TERRA_DIR_HOST: /opt/projects/terra/terra_dsm/external/terra
      TZ: /usr/share/zoneinfo/America/New_York]
    image: terra:terra_me
    volumes:
    - /tmp:/bar:ro
    - source: /opt/projects/terra/terra_dsm/external/terra
      target: /terra
      type: bind
    - /tmp/.X11-unix:/tmp/.X11-unix:ro
    - source: terra-venv
      target: /venv
      type: volume
    - read_only: true
      source: /opt/projects/terra/terra_dsm/external/terra/external/vsi_common
      target: /vsi
      type: bind
version: '3.7'
volumes:
  terra-venv:
    labels:
      com.vsi.just.clean_action: delete
      com.vsi.just.clean_setup: run terra nopipenv true
'''  # noqa


def mock_config(*args, **kwargs):
  return mock_yaml


class TestDockerMap(TestCase):
  class Service:
    compose_service_name = "foo"
    volumes = []

  @mock.patch.object(docker.Compute, 'configService', mock_config)
  def test_config(self):
    compute = docker.Compute()
    service = TestDockerMap.Service()

    with warnings.catch_warnings():
      warnings.simplefilter('ignore')
      volume_map = compute.configuration_map(service)
    self.assertEqual(volume_map, [])

    service.compose_service_name = "terra"
    volume_map = compute.configuration_map(service)

    ans = [('/tmp', '/bar'),
           ('/opt/projects/terra/terra_dsm/external/terra', '/src'),
           ('/opt/projects/terra/terra_dsm/external/terra', '/terra'),
           ('/tmp/.X11-unix', '/tmp/.X11-unix'),
           ('/opt/projects/terra/terra_dsm/external/terra/external/vsi_common',
            '/vsi')]
    self.assertEqual(volume_map, ans)

    service.compose_service_name = "test"
    volume_map = compute.configuration_map(service)
    ans = [('/tmp', '/bar'),
           ('/opt/projects/terra/terra_dsm/external/terra', '/terra'),
           ('/tmp/.X11-unix', '/tmp/.X11-unix'),
           ('/opt/projects/terra/terra_dsm/external/terra/external/vsi_common',
            '/vsi')]
    self.assertEqual(volume_map, ans)

###############################################################################

class SomeService(docker.Service):
  def __init__(self, compose_service_name="launch", compose_file="file1",
               command=["ls"], env={"BAR": "FOO"}):
    self.compose_service_name = compose_service_name
    self.compose_file = compose_file
    self.command = command
    self.env = env
    super().__init__()


def mock_map(self, *args, **kwargs):
  print('WOOT')
  return [('/foo', '/bar'),
          ('/tmp/.X11-unix', '/tmp/.X11-unix')]


class TestDockerService(TestCase):
  # @mock.patch.object(docker.compute, 'configuration_mapService', mock_map)
  def test_service(self):
    pass
    # compute = docker.Compute()
    # compute.configuration_map(SomeService())
    # print(settings._wrapped)
    # print(docker.compute)
    # print(docker.compute.configuration_mapService)
    # print(settings._wrapped)
  #   service = SomeService()
  #   service.pre_run()
  #   setup_dir = service.temp_dir.name
  #   service.post_run()
  #   # Plain test
  #   # f'{str(temp_dir)}:/tmp_settings:rw'

  #   # TERRA_VOLUME 

  #   # TERRA_SOMETHING_VOLUME

  # def test_add_volume(self):
  #   service = SomeService()
  #   self.assertEqual(service.volumes, [])

  #   service.add_volume('/foo', '/bar')
  #   self.assertEqual(service.volumes, [('/foo', '/bar')])
  #   self.assertEqual(service.volumes_flags, [None])

  #   service.add_volume('/data', '/testData', 'ro')
  #   self.assertEqual(service.volumes, [('/foo', '/bar'), ('/data', '/testData')])
  #   self.assertEqual(service.volumes_flags, [None, 'ro'])
