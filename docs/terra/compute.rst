
.. _compute:

=======
Compute
=======

The goal of the compute layer is to offer an abstraction interface between the service runner (the actual algorithm) and the computing model it is running on: be it locally, in a container, a VM, or on the cloud.

Built in computes
-----------------

DummyCompute
^^^^^^^^^^^^

The :py:class:`terra.compute.dummy.Compute` is a debugging tool that simply dry-runs (and logs) what services would have been run.

DockerCompute
^^^^^^^^^^^^^

The :py:class:`terra.compute.docker.Compute` compute is for running in docker containers, creating and running a container for each service that is run. By default, ``docker-compose`` is used by the service definition to run the container. Supports :ref:`settings-path-translation`.

SingularityCompute
^^^^^^^^^^^^^^^^^^

The :py:class:`terra.compute.singularity.Compute` compute is for running in singularity containers, creating and running a container for each service run. By default, :bash:cmd:`just_singularity_functions.bsh singular_defaultify singular-compose` is used by the service definition to run the container. Supports :ref:`settings-path-translation`.

VirtualEnvCompute
^^^^^^^^^^^^^^^^^

The :py:class:`terra.compute.virtualenv.Compute` is used to run services locally in a virtualenv. While terra itself runs in a virtualenv, the terra app has its own virtualenv, which typically exists in the container, but exists locally when using this compute. This compute does not use :ref:`settings-path-translation`.

Using custom computes
---------------------

Todo
