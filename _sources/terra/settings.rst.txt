
.. _settings:

Terra Settings
--------------

.. option:: terra.zone

    Terra can be running in one of three areas of execution, or "zones": the master controller (``controller``), a service runner (``runner``), or a task (``task``). The different zones could all be running on the main host, or other containers or computers, depending on the compute and executor.

    The master controller includes: the CLI, workflow, stage and service definitions layers.

    This variable is automatically updated, and should only be read.

    Default: ``controller``

.. option:: terra.current_service

    The class name of the currently running service. E.g. ``MyAwesomeService_docker``

    The value will be ``None`` before any service has been started. Once a service has started, it will contain the name of that service until the next service starts.

    This variable is automatically updated, and should only be read.

    Default: ``None``

.. _settings-executor:

Executor Settings
-----------------

.. option:: executor.type

    The :py:mod:`concurrent.futures <concurrent.futures>` executor to run tasks. Options are:

        * DummyExecutor
            Doesn't actually run the task, just prints out messages for each task.
        * SyncExecutor
            Runs each task one by one.
        * ThreadPoolExecutor
            Runs each task in its own thread.
        * ProcessPoolExecutor
            Runs each task in its own process.
        * CeleryExecutor
            Runs each task as a celery task. A message broker such as Redis should be initialized.

    Default: ``ThreadPoolExecutor``

    The value of executor.type is a string representing the python path for the selected executor. ``ThreadPoolExecutor`` is actually an alias for ``terra.executor.thread.ThreadPoolExecutor``. Other aliases include:

    ====================================== ==========================================
    Alias                                  Class
    ====================================== ==========================================
    DummyExecutor                          terra.executor.dummy.DummyExecutor
    SyncExecutor                           terra.executor.sync.SyncExecutor
    ThreadPoolExecutor                     terra.executor.thread.ThreadPoolExecutor
    concurrent.futures.ThreadPoolExecutor  terra.executor.thread.ThreadPoolExecutor
    ProcessPoolExecutor                    terra.executor.process.ProcessPoolExecutor
    concurrent.futures.ProcessPoolExecutor terra.executor.process.ProcessPoolExecutor
    CeleryExecutor                         terra.executor.celery.CeleryExecutor
    ====================================== ==========================================

.. note::

   Do not force terra to use :py:class:`concurrent.futures.ThreadPoolExecutor` or :py:class:`concurrent.futures.ProcessPoolExecutor`, as it is missing customizations such as the ``multiprocess`` attribute. You can still :ref:`bring your own executor <custom-executor>`.

.. option:: executor.num_workers

    The maximum number of workers that will be used. Not applicable to :py:class:`terra.executor.sync.SyncExecutor`. Not honored by :py:class:`terra.executor.celery.executor.CeleryExecutor`

    Default: number of cores

.. _settings-compute:

Compute Settings
----------------

.. option:: compute.arch

    The compute architecture which defines how each service will be run. Options are:

    * dummy
        Does nothing but print out messages for every service and task. Useful for testing the app.
    * virtualenv
        Runs services on the host machine, using a python virtual environment.
    * docker
        Runs services on the host machine, inside a docker container.
    * singularity
        Runs services on the host machine, inside a singularity container.

    Default: ``dummy``

.. option:: compute.virtualenv_dir

    Only needed when :option:`compute.arch` is ``virtualenv``. Specifies where the virtual environment's python executable is located.

.. _settings-workflow:

Workflow Settings
-----------------

.. option:: service_start

    For :py:class:`terra.workflow.PipelineWorkflow`, choose which service to start at, if you'd like to skip some of the initial services. Inclusive, so this first service will be run. Options are and of the services in the ``pipeline``, case insensitive.

    Default: ``{First service}``

.. option:: service_end

    For :py:class:`terra.workflow.PipelineWorkflow`, choose which service to end at, if you don't want to run all the way to the end. Inclusive, so this last service will be run. Options are and of the services in the ``pipeline``, case insensitive.

    Default: ``{Last Service}``

.. _settings-logging:

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
