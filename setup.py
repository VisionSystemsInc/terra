from distutils.core import setup

extra_requires = {
  'docker': ['docker-compose'],
  'celery': ["celery[redis]", "flower"]
}

setup(name="terra",
      packages=["terra"],
      description="Terra",
      extra_requires=extra_requires,
      install_requires=[
        "jstyleson",
        "envcontext"
      ]
)
