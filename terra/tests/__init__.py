import os

# Use this as a package level setup
def load_tests(loader, standard_tests, pattern):
  if os.environ.get('TERRA_UNITTEST', None) != "1":
    print('WARNING: Running terra tests without setting TERRA_UNITTEST will '
          'result in side effects such as extraneouse log files being '
          'generated')

  this_dir = os.path.dirname(__file__)
  package_tests = loader.discover(start_dir=this_dir, pattern=pattern)
  standard_tests.addTests(package_tests)
  return standard_tests