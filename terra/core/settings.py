import os
from inspect import isfunction
from functools import wraps

from terra.core.exceptions import ImproperlyConfigured
from terra.core.utils import cached_property
from vsi.tools.python import nested_update, nested_in_dict

try:
  import commentjson as json
except ImportError:
  import json

ENVIRONMENT_VARIABLE = "TERRA_SETTINGS_FILE"


def setting_property(func):
  @wraps(func)
  def wrapper(*args, **kwargs):
    return func(*args, **kwargs)
  wrapper.setting_property = True
  return wrapper


@setting_property
def status_file(self):
  return os.path.join(self.processing_dir, 'status.json')


@setting_property
def processing_dir(self):
  if hasattr(self, 'config_file'):
    return os.path.dirname(self.config_file)
  else:
    return os.getcwd()


# Templates are how we conditionally assign default values. It is a list of 2
# length tuples, where the first in the tuple is a "pattern" and the second
# is the default values. If the pattern is in the settings, then the default
# values are set for any unset values.
global_templates = [
  (
    # Global Defaults
    {},
    {
      "params": {
        "color_elev_thres": 6,
        "azimuth_thres": 90.0,
        "log_level": 10,
        "VisualSFM": "VisualSFM",
        "time_thres_days": 200,
        "dem_res": 1.0,
        "ground_elev": 30.0,
        "dsm_max_height": 180.0,
        "gpu_thread": 2,
        "max_stereo_pair": 600,
        "cpu_thread": 4,
        "max_time": 120,
        "num_active_disparity": 110,
        "n_scene_tile": 64,
        "min_disparity": -220,
        "world_size": 500.0
      },
      'status_file': status_file,
      'processing_dir': processing_dir
    }
  ),
  (
    {"compute": {"type": "terra.compute.dummy"}},  # Pattern
    {"compute": {"value1": "100", "value3": {"value2": "200"}}}  # Defaults
  )
]

# Mixture of django settings


class LazyObject():
  _wrapped = None

  def _setup(self):
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

  def __contains__(self, name):
    if self._wrapped is None:
      self._setup()
    return self._wrapped.__contains__(name)

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
    self._wrapped.config_file = os.environ.get(ENVIRONMENT_VARIABLE)

  def __repr__(self):
    # Hardcode the class name as otherwise it yields 'Settings'.
    if self._wrapped is None:
      return '<LazySettings [Unevaluated]>'
    return str(self._wrapped)

  def configure(self, default_settings={}, **options):
    """
    Called to manually configure the settings. The 'default_settings'
    parameter sets where to retrieve any unspecified values from (its
    argument must support attribute access (__getattr__)).
    """
    if self._wrapped is not None:
      raise RuntimeError('Settings already configured.')
    self._wrapped = Settings(default_settings)
    self._wrapped.update(options)

  @property
  def configured(self):
    """Return True if the settings have already been configured."""
    return self._wrapped is not None


class ObjectDict(dict):
  def __init__(self, *args, **kwargs):
    self.update(*args, **kwargs)

  def __dir__(self):
    d = super().__dir__()
    return list(set(d + [x for x in self.keys()
                         if isinstance(x, str) and x.isidentifier()]))

  def __getattr__(self, name):
    try:
      return self[name]
    except KeyError:
      raise AttributeError("'{}' object has no attribute '{}'".format(
          self.__class__.__name__, name))

  def __setattr__(self, name, value):
    self.update([(name, value)])

  def update(self, *args, **kwargs):
    def patch(self, key):
      ''' Function to patch dict->ObjectDict '''
      value = self[key]

      def patch_list(value):
        ''' List/tuple handler '''
        return [__class__(x) if isinstance(x, dict)
                else patch_list(x) if isinstance(value, (list, tuple))
                else x for x in value]

      if isinstance(value, (list, tuple)):
        self[key] = patch_list(value)
      elif isinstance(value, dict) and not isinstance(value, __class__):
        self[key] = __class__(value)

    # Run nested update first
    nested_update(self, *args, **kwargs)

    # Then search through all the data, for things to patch. And new dicts need
    # to be turned into ObjectDicts
    if args:
      # Handle dict and zipped
      for (key, value) in args[0].items() \
          if isinstance(args[0], dict) else args[0]:
        patch(self, key)

    if kwargs:
      for (key, value) in kwargs.items():
        patch(self, key)


class Settings(ObjectDict):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    for pattern, settings in global_templates:
      if nested_in_dict(pattern, self):
        # Not the most efficient way to do this, but insignificant "preupdate"
        d = {}
        nested_update(d, settings)
        nested_update(d, self)
        # Nested update and run patch code
        self.update(d)

  def __getattr__(self, name):
    # Write a special getattr that will evaluate @setting_property functions
    try:
      val = self[name]
      if isfunction(val) and getattr(val, 'setting_property', None):
        val = val(self)
        self[name] = val
      return val
    except KeyError:
      raise AttributeError("'{}' object has no attribute '{}'".format(
          self.__class__.__name__, name))
