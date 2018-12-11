from distutils.core import setup

setup(name="terra",
      packages=["terra"],
      description="Terra",
      install_requires=[
        "commentjson",
        "docker-compose"
      ]
)
