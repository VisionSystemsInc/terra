from distutils.core import setup

extras_require = {
  'celery': ["celery[redis]"],
  'flower': ["flower"]
}

setup(name="terra",
      packages=["terra"],
      description="Terra",
      extras_require=extras_require,
      install_requires=[
        "pyyaml",
        "jstyleson",
        # I use signal and task from celery, no matter what
        "celery",
        "filelock"
      ]
)
