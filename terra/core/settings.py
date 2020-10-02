'''

A Terra settings file contains all the configuration of your app run. This
document explains how settings work.

The basics
----------

A settings file is just a json file with all your configurations set

.. rubric:: Example

.. code-block:: json

    {
      "compute": {
        "type": "terra.compute.dummy"
      },
      "logging": {
        "level": "DEBUG3"
      }
    }

Designating the settings
------------------------

.. envvar:: TERRA_SETTINGS_FILE

    When you run a Terra App, you have to tell it which settings you’re using.
    Do this by using an environment variable, :envvar:`TERRA_SETTINGS_FILE`.

Default settings
----------------

A Terra settings file doesn’t have to define any settings if it doesn’t need
to. Each setting has a sensible default value. These defaults live in
:data:`global_templates`.

Here’s the algorithm terra uses in compiling settings:

* Load settings from global_settings.py.
* Load settings from the specified settings file, overriding the global
  settings as necessary, in a nested update.

Using settings in Python code
-----------------------------

In your Terra apps, use settings by importing the object
:data:`terra.settings`.

.. rubric:: Example

.. code-block:: python

    from terra import settings

    if settings.params.max_time > 15:
        # Do something

Note that :data:`terra.settings` isn’t a module – it’s an object. So importing
individual settings is not possible:

.. code-block: python

    from terra.settings import params  # This won't work.

Altering settings at runtime
----------------------------

You shouldn’t alter settings in your applications at runtime. For example,
don’t do this in an app:

.. code-block:: python

    from django.conf import settings

    settings.DEBUG = True   # Don't do this!

Available settings
------------------

For a full list of available settings, see the
:ref:`settings reference<settings>`.

Using settings without setting TERRA_SETTINGS_FILE
--------------------------------------------------

In some cases, you might want to bypass the :envvar:`TERRA_SETTINGS_FILE`
environment variable. For example, if you are writing a simple metadata parse
app, you likely don’t want to have to set up an environment variable pointing
to a settings file for each file.

In these cases, you can configure Terra's settings manually. Do this by
calling:

:func:`LazySettings.configure`

.. rubric:: Example:

.. code-block:: python

    from django.conf import settings

    settings.configure(logging={'level': 40})

Pass :func:`setting.configure()<LazySettings.configure>` the same arguments you
would pass to a :class:`dict`, such as keyword arguments as in this example
where each keyword argument represents a setting and its value, or a
:class:`dict`. Each argument name should be the same name as the settings. If a
particular setting is not passed to
:func:`settings.configure()<LazySettings.configure>` and is needed at some
later point, Terra will use the default setting value.

Configuring Terra in this fashion is mostly necessary - and, indeed,
recommended - when you’re using are running a trivial transient app in the
framework instead of a larger application.

'''

# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright notice,
#        this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of Django nor the names of its contributors may be
#        used to endorse or promote products derived from this software without
#        specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
from uuid import uuid4
# from datetime import datetime
from logging.handlers import DEFAULT_TCP_LOGGING_PORT
from inspect import isfunction
from functools import wraps
from json import JSONEncoder
import multiprocessing
import socket
import platform
import warnings
import threading
import concurrent.futures
import copy
from json.decoder import JSONDecodeError

from terra.core.exceptions import (
  ImproperlyConfigured, ConfigurationWarning, handledExitCode
)
# Do not import terra.logger or terra.signals here, or any module that
# imports them
from vsi.tools.python import (
    nested_patch_inplace, nested_patch, nested_update, nested_in_dict
)

try:
  import jstyleson as json
except ImportError:  # pragma: no cover
  import json

ENVIRONMENT_VARIABLE = "TERRA_SETTINGS_FILE"
'''str: The environment variable that store the file name of the configuration
file
'''

filename_suffixes = ['_file', '_files', '_dir', '_dirs', '_path', '_paths']
'''list: The list key suffixes that are to be considered for volume translation
'''

json_include_suffixes = ['_json']
'''list: The list key suffixes that are to be considered executing json
include replacement at load time.
'''


def settings_property(func):
  '''
  Functions wrapped with this decorator will only be called once, and the value
  from the call will be cached, and replace the function altogether in the
  settings structure, similar to a cached lazy evaluation

  One settings_property can safely reference another settings property, using
  ``self``, which will refer to the :class:`Settings` object

  Arguments
  ---------
  func : :term:`function`
      Function being decorated
  '''

  @wraps(func)
  def wrapper(*args, **kwargs):
    return func(*args, **kwargs)

  wrapper.settings_property = True
  return wrapper


@settings_property
def status_file(self):
  '''
  The default :func:`settings_property` for the status_file. The default is
  :func:`processing_dir/status.json<processing_dir>`
  '''
  return os.path.join(self.processing_dir, 'status.json')


@settings_property
def settings_dir(self):
  '''
  The default :func:`settings_property` for settings dumps as JSON files.
  The default is :func:`processing_dir/settings<processing_dir>`.
  This directory is not used if ``TERRA_DISABLE_SETTINGS_DUMP`` is true.
  '''
  return os.path.join(self.processing_dir, 'settings')


@settings_property
def processing_dir(self):
  '''
  The default :func:`settings_property` for the processing directory. If not
  set in your configuration, it will default to the directory where the config
  file is stored. If this is not possible, it will use the current working
  directory.

  If the directory is not writeable, a temporary directory will be used instead
  '''
  try:
    processing_dir = os.path.dirname(self.terra.config_file)
  except Exception:
    processing_dir = os.getcwd()
    logger.warning('No config file found, and processing dir unset. '
                   f'Using cwd: {processing_dir}')

  if not os.access(processing_dir, os.W_OK):
    import tempfile
    bad_dir = processing_dir
    processing_dir = tempfile.mkdtemp(prefix="terra_")
    logger.error(f'You do not have access to processing dir: "{bad_dir}". '
                 f'Using "{processing_dir}" instead')

  return processing_dir


@settings_property
def config_file(self):
  '''
  A :func:`settings_property` for passing the filename of the config_file to
  settings
  '''
  # There was a chicken-egg problem with determing settings.processing_dir:
  # #. Call ``_setup``
  #   #. Calls ``configure``
  #   #. Send signal
  #     #. Logger receives signal, and start setting up logger
  #     #. Needs to know where to put log files, so check
  #        ``settings.processing_dir``
  #     #. settings.processing_dir looks for `setttings.terra.config_file``,
  #        doesn't see it yet
  # 2. Returns to ``_setup``
  # #. Then set ``settings.terra.config_file``, but it's too late
  # This will around the problem
  return config_file.filename


config_file.filename = None


@settings_property
def unittest(self):
  '''
  A :func:`settings_property` for determing if unittests are running or not

  Checks the value of :envvar:`TERRA_UNITTEST` and returns True or False based
  off of that.
  '''

  return os.environ.get('TERRA_UNITTEST', None) == "1"


@settings_property
def need_to_set_virtualenv_dir(self):
  warnings.warn("You are using the virtualenv compute, and did not set "
                "settings.compute.virtualenv_dir in your config file. "
                "Using system python.", ConfigurationWarning)
  return None


@settings_property
def terra_uuid(self):
  return str(uuid4())


@settings_property
def logging_hostname(self):
  '''
  A :func:`settings_property` for getting the hostname for logging.
  Should the env. variable ``TERRA_RESOLVE_HOSTNAME = 1``, this function
  will attempt to resolve the IP address of the default host route as per
  https://stackoverflow.com/a/28950776.
  '''
  if os.environ.get('TERRA_RESOLVE_HOSTNAME', None) == "1":
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      # doesn't even have to be reachable
      s.connect(('10.255.255.255', 1))
      ip_addr = s.getsockname()[0]
      return ip_addr
    except OSError:
      pass
    finally:
      s.close()

  # default return
  return platform.node()


@settings_property
def logging_listen_address(self):
  '''
  A :func:`settings_property` defining the address on which the main
  logger will listen. In some environments this may need to be overridden
  (e.g., ``0.0.0.0``) to ensure appropriate capture of service & task logs.
  '''

  # is 0.0.0.0 as default better?
  return self.logging.server.hostname


global_templates = [
  (
    # Global Defaults
    {},
    {
      "logging": {
        "level": "ERROR",
        "format": "%(asctime)s (%(hostname)s:%(zone)s): "
                  "%(levelname)s/%(processName)s - %(filename)s - %(message)s",
        "date_format": None,
        "style": "%",
        "server": {
          # This is tricky use of a setting, because the master controller will
          # be the first to set it, but the runner and task will inherit the
          # master controller's values, not their node names, should they be
          # different (such as celery and spark)
          "hostname": logging_hostname,
          "port": DEFAULT_TCP_LOGGING_PORT,
          "listen_address": logging_listen_address,
        }
      },
      "executor": {
        "num_workers": multiprocessing.cpu_count(),
        "type": "ProcessPoolExecutor",
        'volume_map': []
      },
      "compute": {
        "arch": "terra.compute.dummy",
        'volume_map': []
      },
      'terra': {
        'config_file': config_file,
        # unlike other settings, this should NOT be overwritten by a
        # config.json file, there is currently nothing to prevent that
        'zone': 'controller',
        # 'start_time': datetime.now(), # Not json serializable yet
        'uuid': terra_uuid
      },
      "service_start": None,
      "service_end": None,
      'settings_dir': settings_dir,
      'status_file': status_file,
      'processing_dir': processing_dir,
      'unittest': unittest,
      'resume': False
    }
  ),
  (
    {"compute": {"arch": "terra.compute.virtualenv"}},  # Pattern
    {"compute": {"virtualenv_dir": need_to_set_virtualenv_dir}}  # Defaults
  ),
  (  # So much for DRY :(
    {"compute": {"arch": "virtualenv"}},
    {"compute": {"virtualenv_dir": need_to_set_virtualenv_dir}}
  )
]
''':class:`list` of (:class:`dict`, :class:`dict`): Templates are how we
conditionally assign default values. It is a list of pair tuples, where the
first in the tuple is a "pattern" and the second is the default values. If the
pattern is in the settings, then the default values are set for any unset
values.

Values are copies recursively, but only if not already set by your settings.'''


class LazyObject:
  '''
  A wrapper class that lazily evaluates (calls :func:`LazyObject._setup`)

  :class:`LazyObject` remains unevaluated until one of the supported magic
  functions are called.

  Based off of Django's LazyObject
  '''

  '''
  The internal object being wrapped
  '''

  def _setup(self):
    """
    Abstract. Must be implemented by subclasses to initialize the wrapped
    object.

    Raises
    ------
    NotImplementedError
        Will throw this exception unless a subclass redefines :func:`_setup`
    """
    raise NotImplementedError(
        'subclasses of LazyObject must provide a _setup() method')

  def __init__(self):
    self._wrapped = None

  def __getattr__(self, name, *args, **kwargs):
    '''Supported'''
    if self._wrapped is None:
      self._setup()
    return getattr(self._wrapped, name, *args, **kwargs)

  def __setattr__(self, name, value):
    '''Supported'''
    if name in ("_wrapped", "__class__"):
      # Call super to avoid infinite __setattr__ loops.
      super().__setattr__(name, value)
    else:
      if self._wrapped is None:
        self._setup()
      setattr(self._wrapped, name, value)

  def __delattr__(self, name):
    '''Supported'''
    if name == "_wrapped":
      raise TypeError("can't delete _wrapped.")
    if self._wrapped is None:
      self._setup()
    delattr(self._wrapped, name)

  def __dir__(self):
    """ Supported """
    d = super().__dir__()
    if self._wrapped is not None:
      return list(set(d + dir(self._wrapped)))
    return d

  def __getitem__(self, name):
    '''Supported'''
    if self._wrapped is None:
      self._setup()
    return self._wrapped[name]

  def __setitem__(self, name, value):
    '''Supported'''
    if self._wrapped is None:
      self._setup()
    self._wrapped[name] = value

  def __delitem__(self, name):
    '''Supported'''
    if self._wrapped is None:
      self._setup()
    del(self._wrapped[name])

  def __len__(self):
    '''Supported'''
    if self._wrapped is None:
      self._setup()
    return self._wrapped.__len__()

  def __contains__(self, name):
    '''Supported'''
    if self._wrapped is None:
      self._setup()
    return self._wrapped.__contains__(name)

  def __iter__(self):
    '''Supported'''
    if self._wrapped is None:
      self._setup()
    return iter(self._wrapped)


class LazySettings(LazyObject):
  '''
  A :class:`LazyObject` proxy for either global Terra settings or a custom
  settings object. The user can manually configure settings prior to using
  them. Otherwise, Terra uses the config file pointed to by
  :envvar:`TERRA_SETTINGS_FILE`

  Based off of :mod:`django.conf`
  '''

  def _setup(self, name=None):
    """
    Load the config json file pointed to by the environment variable. This is
    used the first time settings are needed, if the user hasn't configured
    settings manually.

    Arguments
    ---------
    name : :class:`str`, optional
        The name used to describe the settings object. Defaults to ``settings``

    Raises
    ------
    ImproperlyConfigured
        If the settings has already been configured, will throw an error. Under
        normal circumstances, :func:`_setup` will not be called a second time.
    """
    settings_file = os.environ.get(ENVIRONMENT_VARIABLE)
    if not settings_file:
      desc = ("setting %s" % name) if name else "settings"
      raise ImproperlyConfigured(
          "Requested %s, but settings are not configured. "
          "You must either define the environment variable %s "
          "or call settings.configure() before accessing settings." %
          (desc, ENVIRONMENT_VARIABLE))
    # Store in global variable :-\
    config_file.filename = settings_file
    self.configure(json_load(settings_file))

  def __getstate__(self):
    if self._wrapped is None:
      self._setup()
    return {'_wrapped': self._wrapped}

  def __setstate__(self, state):
    self._wrapped = state['_wrapped']

    # This should NOT be done on a per instance basis, this is only for
    # the global terra.settings. So maybe this should be done in a context
    # manager??
    # from terra.core.signals import post_settings_configured
    # post_settings_configured.send(sender=self)

  def __repr__(self):
    # Hardcode the class name as otherwise it yields 'Settings'.
    if self._wrapped is None:
      return '<LazySettings [Unevaluated]>'
    return str(self._wrapped)

  def configure(self, *args, **kwargs):
    """
    Called to manually configure the settings. The 'default_settings'
    parameter sets where to retrieve any unspecified values from (its
    argument should be a :class:`dict`).

    Arguments
    ---------
    *args :
        Passed along to :class:`Settings`
    **kwargs :
        Passed along to :class:`Settings`

    Raises
    ------
    ImproperlyConfigured
        If settings is already configured, will throw this exception
    """
    if self._wrapped is not None:
      raise ImproperlyConfigured('Settings already configured.')
    logger.debug2('Pre settings configure')
    self._wrapped = Settings(*args, **kwargs)

    for pattern, settings in global_templates:
      if nested_in_dict(pattern, self._wrapped):
        # Not the most efficient way to do this, but insignificant "preupdate"
        d = {}
        nested_update(d, settings)
        nested_update(d, self._wrapped)
        # Nested update and run patch code
        self._wrapped.update(d)

    def read_json(json_file):
      # In case json_file is an @settings_property function
      if getattr(json_file, 'settings_property', None):
        json_file = json_file(settings)

      return Settings(json_load(json_file))

    nested_patch_inplace(
        self._wrapped,
        lambda key, value: (isinstance(key, str)
                            and (isinstance(value, str)
                                 or getattr(value, 'settings_property', False))
                            and any(key.endswith(pattern)
                                    for pattern in json_include_suffixes)),
        lambda key, value: read_json(value))

    # Importing these here is intentional, it guarantees the signals are
    # connected so that executor and computes can setup logging if need be
    import terra.executor  # noqa
    import terra.compute  # noqa

    from terra.core.signals import post_settings_configured
    post_settings_configured.send(sender=self)
    logger.debug2('Post settings configure')

  @property
  def configured(self):
    """
    Check if the settings have already been configured

    Returns
    -------
    bool
      Return ``True`` if has already been configured
    """
    return self._wrapped is not None

  def add_templates(self, templates):
    """
    Helper function to easily expose adding more defaults templates to
    :data:`global_templates` specific for an application

    Arguments
    ---------
    templates : list
      A list of pairs of dictionaries just like :data:`global_templates`
    """
    # Pre-extend
    offset = len(global_templates)
    for template in templates:
      global_templates.insert(-offset, template)

  def __enter__(self):
    if self._wrapped is None:
      self._setup()
    return self._wrapped.__enter__()

  def __exit__(self, exc_type=None, exc_value=None, traceback=None):
    return_value = self._wrapped.__exit__(exc_type, exc_value, traceback)

    # Incase the logger was messed with in the context, reset it.
    from terra.core.signals import post_settings_context
    post_settings_context.send(sender=self, post_settings_context=True)

    return return_value


class LazySettingsThreaded(LazySettings):
  @classmethod
  def downcast(cls, obj):
    # This downcast function was intended for LazySettings instances only
    assert type(obj) == LazySettings
    # Put settings in __wrapped where property below expects it.
    settings = obj._wrapped
    # Downcast
    obj.__class__ = cls
    obj.__wrapped = settings
    obj.__tls = threading.local()

  @property
  def _wrapped(self):
    '''
    Thread safe version of _wrapped getter
    '''
    thread = threading.current_thread()
    if thread._target == concurrent.futures.thread._worker:
      if not hasattr(self.__tls, 'settings'):
        self.__tls.settings = copy.deepcopy(self.__wrapped)
      return self.__tls.settings
    else:
      return self.__wrapped

  def __setattr__(self, name, value):
    '''Supported'''
    if name in ("_LazySettingsThreaded__wrapped",
                "_LazySettingsThreaded__tls"):
      # Call original __setattr__ to avoid infinite __setattr__ loops.
      object.__setattr__(self, name, value)
    else:
      # Normal LazyObject setter
      super().__setattr__(name, value)


class ObjectDict(dict):
  '''
  An object dictionary, that accesses dictionary keys using attributes (``.``)
  rather than items (``[]``).
  '''

  def __init__(self, *args, **kwargs):
    self.update(*args, **kwargs)

  def __dir__(self):
    """ Supported """
    d = super().__dir__()
    return list(set(d + [x for x in self.keys()
                         if isinstance(x, str) and x.isidentifier()]))

  def __getattr__(self, name):
    """ Supported """
    try:
      return self[name]
    except KeyError:
      raise AttributeError("'{}' object has no attribute '{}'".format(
          self.__class__.__qualname__, name)) from None

  def __setattr__(self, name, value):
    """ Supported """
    self.update([(name, value)])

  def __contains__(self, name):
    if '.' in name:
      first, rest = name.split('.', 1)
      return self.__contains__(first) and (rest in self[first])
    return super().__contains__(name)

  def update(self, *args, **kwargs):
    """ Supported """

    nested_update(self, *args, **kwargs)


class ExpandedString(str):
  pass


class Settings(ObjectDict):
  def __getattr__(self, name):
    '''
    ``__getitem__`` that will evaluate @settings_property functions, and cache
    the values
    '''

    # This is here instead of in LazySettings because the functor is given
    # LazySettings, but then if __getattr__ is called on that, the segment of
    # the settings object that is retrieved is of type Settings, therefore
    # the settings_property evaluation has to be here.

    try:
      val = self[name]
      if isfunction(val) and getattr(val, 'settings_property', None):
        # Ok this ONE line is a bit of a hack :( But I argue it's specific to
        # this singleton implementation, so I approve!
        val = val(settings)

        # cache result, because the documentation said this should happen
        self[name] = val

      if isinstance(val, str) and not isinstance(val, ExpandedString):
        val = os.path.expandvars(val)
        if any(name.endswith(pattern) for pattern in filename_suffixes):
          val = os.path.expanduser(val)
        val = ExpandedString(val)
        self[name] = val
      return val
    except KeyError:
      # Throw a KeyError to prevent a recursive corner case
      raise AttributeError("'{}' object has no attribute '{}'".format(
          self.__class__.__qualname__, name)) from None

  def __enter__(self):
    import copy
    try:
      # check if _backup exists
      backup = object.__getattribute__(self, "_backup")
      # if it does, append a copy of self
      backup.append(copy.deepcopy(self))
    except AttributeError:
      # if it doesn't exist yet, make a list
      object.__setattr__(self, "_backup", [copy.deepcopy(self)])

  def __exit__(self, type_, value, traceback):
    self.clear()
    backup = self._backup.pop()
    self.update(backup)


settings = LazySettings()
'''LazySettings: The setting object to use through out all of terra'''


class TerraJSONEncoder(JSONEncoder):
  '''
  Json serializer for :class:`LazySettings`.

  .. note::

      Does not work on :class:`Settings` since it would be handled
      automatically as a :class:`dict`.
  '''

  def default(self, obj):
    if isinstance(obj, LazySettings):
      if obj._wrapped is None:
        raise ImproperlyConfigured('Settings not initialized')
      return TerraJSONEncoder.serializableSettings(obj._wrapped)
    # elif isinstance(obj, datetime):
    #   return str(obj)
    return JSONEncoder.default(self, obj)  # pragma: no cover

  @staticmethod
  def serializableSettings(obj):
    '''
    Convert a :class:`Settings` object into a json serializable :class:`dict`.

    Since :class:`Settings` can contain :func:`settings_property`, this
    prevents json serialization. This function will evaluate all
    :func:`settings_property`'s for you.

    Arguments
    ---------
    obj: :class:`Settings` or :class:`LazySettings`
        Object to be converted to json friendly :class:`Settings`
    '''

    if isinstance(obj, LazySettings):
      obj = obj._wrapped

    # I do not os.path.expandvars(val) here, because the Just-docker-compose
    # takes care of that for me, so I can still use the envvar names in the
    # containers

    obj = nested_patch(
        obj,
        lambda k, v: isfunction(v) and hasattr(v, 'settings_property'),
        lambda k, v: v(obj))

    obj = nested_patch(
        obj,
        lambda k, v: any(v is not None and isinstance(k, str)
                         and k.endswith(pattern)
                         for pattern in filename_suffixes),
        lambda k, v: os.path.expanduser(v))

    return obj

  @staticmethod
  def dumps(obj, **kwargs):
    '''
    Convenience function for running `dumps` using this encoder.

    Arguments
    ---------
    obj: :class:`LazySettings`
        Object to be converted to json friendly :class:`dict`
    '''
    return json.dumps(obj, cls=TerraJSONEncoder, **kwargs)


def json_load(filename):
  # Helper function to load from json
  try:
    with open(filename, 'r') as fid:
      return json.load(fid)
  except JSONDecodeError as e:
    logger.critical(
        f'Error parsing the JSON config file {filename}: ' + str(e))
    raise SystemExit(handledExitCode)
  except FileNotFoundError as e:
    logger.critical('Cannot find JSON config file: ' + str(e))
    raise SystemExit(handledExitCode)


import terra.logger  # noqa
logger = terra.logger.getLogger(__name__)
