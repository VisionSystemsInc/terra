from distutils.core import setup

extra_requires = {
  'celery': ["celery[redis]"],
  'flower': ["flower"]
}

setup(name="terra",
      packages=["terra"],
      description="Terra",
      extra_requires=extra_requires,
      install_requires=[
        "pyyaml",
        "jstyleson",
        # I use signal and task from celery, no matter what
        "celery",
        "filelock>=3.12"
      ]
)
