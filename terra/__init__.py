import os

from _terra import *

from terra.exceptions import ImproperlyConfigured

try:
  import commentjson as json
except ImportError:
  import json

ENVIRONMENT_VARIABLE = "TERRA_SETTINGS_FILE"

# Mixture of django settings


class LazyObject():
  _wrapped = None

  def _setup():
    """
    Must be implemented by subclasses to initialize the wrapped object.
    """
    raise NotImplementedError(
        'subclasses of LazyObject must provide a _setup() method')

  def __init__(self):
    self._wrapped = None

  def __getattr__(self, name, default=None):
    if self._wrapped is None:
      self._setup()
    return getattr(self._wrapped, name, default)

  def __getitem__(self, name):
    if self._wrapped is None:
      self._setup()
    return self._wrapped[name]

  def __setattr__(self, name, value):
    if name == "_wrapped":
      # Assign to __dict__ to avoid infinite __setattr__ loops.
      self.__dict__["_wrapped"] = value
    else:
      if self._wrapped is None:
        self._setup()
      setattr(self._wrapped, name, value)

  def __setitem__(self, name, value):
    if name == "_wrapped":
      # Assign to __dict__ to avoid infinite __setattr__ loops.
      self.__dict__["_wrapped"] = value
    else:
      if self._wrapped is None:
        self._setup()
      self._wrapped[name] = value

  def __delattr__(self, name):
    if name == "_wrapped":
      raise TypeError("can't delete _wrapped.")
    if self._wrapped is None:
      self._setup()
    delattr(self._wrapped, name)


class LazySettings(LazyObject):
  def _setup(self, name=None):
    settings_file = os.environ.get(ENVIRONMENT_VARIABLE)
    if not settings_file:
      desc = ("setting %s" % name) if name else "settings"
      raise ImproperlyConfigured(
          "Requested %s, but settings are not configured. "
          "You must either define the environment variable %s "
          "or call settings.configure() before accessing settings."
          % (desc, ENVIRONMENT_VARIABLE))
    with open(settings_file) as fid:
      self._wrapped = Settings(json.load(fid))

  def __repr__(self):
    # Hardcode the class name as otherwise it yields 'Settings'.
    if self._wrapped is None:
      return '<LazySettings [Unevaluated]>'
    return '<LazySettings>'

  def configure(self, default_settings={}, **options):
    """
    Called to manually configure the settings. The 'default_settings'
    parameter sets where to retrieve any unspecified values from (its
    argument must support attribute access (__getattr__)).
    """
    if self._wrapped is not None:
      raise RuntimeError('Settings already configured.')
    holder = Settings(default_settings)
    for name, value in options.items():
      setattr(holder, name, value)
    self._wrapped = holder

  @property
  def configured(self):
    """Return True if the settings have already been configured."""
    return self._wrapped is not None


class Settings(dict):
  def __init__(self, *args, **kwargs):
    self.update(*args, **kwargs)
    for k in self.__class__.__dict__.keys():
      if not (k.startswith('__') and k.endswith('__')) and not k in ('update',
                                                                     'pop'):
        setattr(self, k, getattr(self, k))

  def __setattr__(self, name, value):
    if isinstance(value, (list, tuple)):
      value = [self.__class__(x)
               if isinstance(x, dict) else x for x in value]
    elif isinstance(value, dict) and not isinstance(value, self.__class__):
      value = self.__class__(value)
    super().__setattr__(name, value)
    super().__setitem__(name, value)

  __setitem__ = __setattr__

  def update(self, *args, **kwargs):
    if args and args[0]:
      assert(len(args) == 1)
      d = args[0]
    else:
      d = dict()
    if kwargs:
      d.update(kwargs)
    for k, v in d.items():
      setattr(self, k, v)

  def pop(self, k, d=None):
    delattr(self, k)
    return super().pop(k, d)


settings = LazySettings()
