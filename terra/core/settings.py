import os

from terra.core.exceptions import ImproperlyConfigured

try:
  import commentjson as json
except ImportError:
  import json

ENVIRONMENT_VARIABLE = "TERRA_SETTINGS_FILE"
# Place holder for "default settings"
global_settings = {"processing_dir": os.getcwd()}

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

  def configure(self, default_settings=global_settings, **options):
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
    def patch(self, key, value):
      def patch_list(value):
        return [__class__(x) if isinstance(x, dict)
                else patch_list(x) if isinstance(value, (list, tuple))
                else x for x in value]
      if isinstance(value, (list, tuple)):
        self[key] = patch_list(value)
      elif isinstance(value, dict) and not isinstance(value, __class__):
        self[key] = __class__(value)

    # Run super update first, like normal
    super().update(*args, **kwargs)

    # Then search through all the data, for things to patch
    if args:
      # Handle dict and zipped
      for (key, value) in args[0].items() \
          if isinstance(args[0], dict) else args[0]:  # noqa
        patch(self, key, value)

    if kwargs:
      for (key, value) in kwargs.items():
        patch(self, key, value)


class Settings(ObjectDict):
  def __init__(self, *args, **kwargs):
    self.update(**global_settings)
    super().__init__(*args, **kwargs)

  @property
  def status_file(self):
    return os.path.join(self.processing_dir, 'status.json')
