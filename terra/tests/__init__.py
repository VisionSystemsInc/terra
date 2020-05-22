import os
import warnings

# from terra.core.signals import logger_configure, logger_reconfigure


# # Disconnect signal receivers
# logger_configure.receivers = []
# logger_reconfigure.receivers = []


# Use this as a package level setup
def load_tests(loader, standard_tests, pattern):
  if os.environ.get('TERRA_UNITTEST', None) != "1":
    warnings.warn('WARNING: Running terra tests without setting TERRA_UNITTEST will '
          'result in side effects such as extraneouse log files being '
          'generated')

  this_dir = os.path.dirname(__file__)
  package_tests = loader.discover(start_dir=this_dir, pattern=pattern)
  standard_tests.addTests(package_tests)

  # Run this test last, to make sure none of the other tests degrated the
  # integrity of terra. A configured terra can cause unittests to interfere
  # with each other
  loader.testMethodPrefix = 'last'
  package_tests = loader.discover(start_dir=this_dir, pattern=pattern)
  standard_tests.addTests(package_tests)

  # This does not check THIS file for 'last', I can't figure that out, cause
  # it is "discovered" before load_tests is ever called
  return standard_tests
