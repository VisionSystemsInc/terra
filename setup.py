from distutils.core import setup

setup(name="terra",
      packages=["terra"],
      description="Terra",
      install_requires=[
        "jstyleson",
        "docker-compose",
        "envcontext",
        "celery[redis]",
        "flower"
      ]
)
