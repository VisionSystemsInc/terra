
.. _settings:

Terra Settings
--------------

.. option:: terra.zone

    Terra can be running in one of three areas of execution, or "zones": the master controller (``controller``), a service runner (``runner``), or a task (``task``). The different zones could all be running on the main host, or other containers or computers, depending on the compute and executor.

    The master controller includes: the CLI, workflow, stage and service definitions layers.

    This variable is automatically updated, and should only be read.

    Default: ``controller``

Workflow Settings
-----------------

.. option:: service_start

    For :py:class:`terra.workflow.PipelineWorkflow`, choose which service to start at, if you'd like to skip some of the initial services. Inclusive, so this first service will be run. Options are and of the services in the ``pipeline``, case insensitive.

    Default: ``{First service}``

.. option:: service_end

    For :py:class:`terra.workflow.PipelineWorkflow`, choose which service to end at, if you don't want to run all the way to the end. Inclusive, so this last service will be run. Options are and of the services in the ``pipeline``, case insensitive.

    Default: ``{Last Service}``

.. _settings_logging:

Logging Settings
----------------

.. option:: logging.level

  The logging level, set by using either a string (e.g. ``WARNING``) or a number (e.g. ``30``)

.. option:: logging.format

  The logging output format.
  https://docs.python.org/3/library/logging.html#logrecord-attributes. Default:
  ``%(asctime)s : %(levelname)s - %(message)s``

.. option:: logging.date_format

  The date format. Default: ``None``

.. option:: logging.format_style

  The format style, ``%``, ``{``, or ``$`` notation. Default: ``%``
