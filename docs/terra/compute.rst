
.. _compute:

=======
Compute
=======

The goal of the compute layer is to offer an abstraction interface between the service runner (the actual algorithm) and the computing platform it is running on: be it locally, in a cluster, a grid, or on the cloud.

Built in computes
-----------------

DummyCompute
^^^^^^^^^^^^

The :py:class:`terra.compute.dummy.Compute` is a debugging tool that simply dry-runs (and logs) what services would have been run.

DockerCompute
^^^^^^^^^^^^^

The :py:class:`terra.compute.docker.Compute` compute is for running in docker containers, creating and running a container for each service that is run. By default, ``docker compose`` is used by the service definition to run the container. Supports :ref:`settings-path-translation`.

SingularityCompute
^^^^^^^^^^^^^^^^^^

The :py:class:`terra.compute.singularity.Compute` compute is for running in singularity containers, creating and running a container for each service run. By default, :bash:cmd:`just_singularity_functions.bsh singular_defaultify singular-compose` is used by the service definition to run the container. Supports :ref:`settings-path-translation`.

VirtualEnvCompute
^^^^^^^^^^^^^^^^^

The :py:class:`terra.compute.virtualenv.Compute` is used to run services locally in a virtualenv. While terra itself runs in a virtualenv, the terra app has its own virtualenv, which typically exists in the container, but exists locally when using this compute. This compute does not use :ref:`settings-path-translation`.

Debugging in the compute
------------------------

In order to debug in the exact compute environment, two environment were introduced to help:

.. envvar:: TERRA_DEBUG_SERVICE

Since there are many complicated steps that go into starting an environment for a service runner (i.e. starting a docker container with the right mounts and temporary settings file). Setting :envvar:`TERRA_DEBUG_SERVICE` will start the environment and run the command :envvar:`TERRA_DEBUG_SHELL` to allow you to debug in the actual environment with ease. :envvar:`TERRA_DEBUG_SERVICE` must be set to the service runner name or any class in it's class hierarchy (e.g. ``MyServiceRunner_docker``, ``MyServiceRunner``, or to stop on all runners ``object``).

.. envvar:: TERRA_DEBUG_SHELL

The command that is when the service is debugged. Default: ``bash``, but you can set it to anything (e.g. ``bash --rcfile "/test_argument/dir with spaces/my.rc"``).

Using custom computes
---------------------

Todo
