import os
import sys
import platform
import traceback

ranButFailedExitCode = 62  # 20 + 5 + 18 + 18 + 1


class NoStackException(Exception):
  """
  An exception class that when unhandled, does not print the stack trace

  Still behaves like an exception, but ideal for errors that you don't want to
  clutter the screen with stack traces, because the error message is all you
  need to know. E.g. "File not found", you just need the filename.
  """


NO_STACK_EXCEPTIONS = (NoStackException,)
"""tuple: A tuple of Exceptions classes that will not
"""

# TODO: Rewrite both functions as a singleton class


def setup_logging_exception_hook():
  '''
  Setup logging of uncaught exceptions

  MITM insert an error logging call on all uncaught exceptions. Should only
  be called once, or else errors will be logged multiple times
  '''

  original_hook = sys.excepthook

  # https://stackoverflow.com/a/16993115/4166604
  def handle_exception(exc_type, exc_value, exc_traceback):
    # Try catch here because I want to make sure the original hook is called
    try:
      from terra.logger import getLogger
      getLogger(__name__).critical("Uncaught exception",
                                   extra={'skip_stderr': True},
                                   exc_info=(exc_type,
                                             exc_value,
                                             exc_traceback))

      # Skip calling the original_hook when I don't want to print the stack
      if issubclass(exc_type, NO_STACK_EXCEPTIONS):
        print(f'ERROR: ({exc_type.__name__}) {exc_value}', file=sys.stderr)
        if hasattr(sys, 'ps1'):  # If interactive mode
          return original_hook(exc_type, exc_value, exc_traceback)
        sys.exit(ranButFailedExitCode)

    except Exception:  # pragma: no cover
      print('There was an exception logging in the exception handler!',
            file=sys.stderr)
      traceback.print_exc()

    try:
      from terra import settings
      zone = settings.terra.zone
    except Exception:
      zone = 'preconfig'
    print(f'Exception in {zone} on {platform.node()}',
          file=sys.stderr)

    if hasattr(sys, 'ps1'):  # If interactive mode
      return original_hook(exc_type, exc_value, exc_traceback)

    try:
      # sys.executable for frozen, untested?

      # May not work when frozen or various other corner cases. Interactive
      # python/Jupyter
      spec = sys.modules['__main__'].__spec__
      if spec is None:
        # Interactive, just use cwd and hope for best
        main_dirs = [os.getcwd()]
      else:
        top_module = sys.modules.get(spec.name.split('.')[0])
        if top_module:
          spec = top_module.__spec__

        try:
          main_dirs = [os.path.dirname(spec.origin)]
        except AttributeError:
          main_dirs = spec.submodule_search_locations

      extracted_summary = traceback.extract_tb(exc_traceback)

      our_scripts = [any(x.filename.startswith(main_dir)
                     for main_dir in main_dirs) for x in extracted_summary]

      msg = extracted_summary.format()
      msg = ['\x1b[31m' + msg + '\x1b[0m'
             if color else msg
             for msg, color in zip(extracted_summary.format(), our_scripts)]
      msg = ''.join(msg)
      msg += '\x1b[33m' + \
             ''.join(traceback.format_exception_only(exc_type, exc_value)) + \
             '\x1b[0m'
      print(msg, file=sys.stderr, end='')
      sys.exit(ranButFailedExitCode)
    except Exception:
      return original_hook(exc_type, exc_value, exc_traceback)

  # Replace the hook
  sys.excepthook = handle_exception


# https://stackoverflow.com/a/49176714/4166604
def setup_logging_ipython_exception_hook():
  '''
  Setup logging of uncaught exceptions in ipython

  MITM insert an error logging call on all uncaught exceptions. Should only
  be called once, or else errors will be logged multiple times

  If IPython cannot be imported, nothing happens.
  '''
  try:
    import warnings
    with warnings.catch_warnings():
      warnings.simplefilter('ignore')
      from IPython.core.interactiveshell import InteractiveShell

    original_exception = InteractiveShell.showtraceback

    def handle_traceback(*args, **kwargs):  # pragma: no cover
      try:
        from terra.logger import getLogger
        getLogger(__name__).critical("Uncaught exception",
                                     extra={'skip_stderr': True},
                                     exc_info=sys.exc_info())

        # Skip calling the original_hook when I don't want to print the stack
        if issubclass(sys.exc_info()[0], NO_STACK_EXCEPTIONS):
          print(f'ERROR: {sys.exc_info()[1]}', file=sys.stderr)
          return
      except Exception:
        print('There was an exception logging in the exception handler!',
              file=sys.stderr)
        traceback.print_exc()

      try:
        from terra import settings
        zone = settings.terra.zone
      except Exception:
        zone = 'preconfig'
      print(f'Exception in {zone} on {platform.node()}',
            file=sys.stderr)

      return original_exception(*args, **kwargs)

    InteractiveShell.showtraceback = handle_traceback

  except ImportError:  # pragma: no cover
    pass


class ImproperlyConfigured(NoStackException):
  """
  Exception for Terra is somehow improperly configured
  """


class NoStackValueError(NoStackException, ValueError):
  pass


NoStackValueError.__name__ = 'ValueError'


class ConfigurationWarning(Warning):
  """
  Warning that Terra may be improperly configured
  """
