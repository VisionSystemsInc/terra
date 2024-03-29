
.. _executor:

========
Executor
========

In Terra, an executor is a class based on :py:class:`concurrent.futures.Executor` that is used in order to utilize a single API to execute tasks in parallel using: single threaded, multithreaded, multiprocess, or distributed computer environments. See :mod:`concurrent.futures` for more information on how to use executors.

An app need not be limited to always using one type of executor, but the default executor type used will be set by :option:`executor.type`.

A terra task is a function with the :py:func:`terra.task.shared_task` decorator (based on :ref:`@shared_task<celery:task-basics>`). :py:func:`terra.task.shared_task` decorator should be used, and not :py:class:`terra.task.TerraTask`, since not all executors utilize celery, and tasks should work with all executors, not just celery. ``bind`` is turned on by default, so all task functions need to have a ``self`` as the first argument.

It is good practice to only get filenames from terra settings, and not by reading other files from disk. Tasks can also get filenames from keyword arguments since both task keyword arguments and settings supports :ref:`settings-path-translation`.

Built in executors
------------------

DummyExecutor
^^^^^^^^^^^^^

The :py:class:`terra.executor.dummy.DummyExecutor` is a debugging tool that simply dry-runs (and logs) what tasks would have been run.

SyncExecutor
^^^^^^^^^^^^

The :py:class:`terra.executor.sync.SyncExecutor` is a single-threaded executor that runs the tasks synchronously in serial. It is often used as a tool for debugging race conditions.

ThreadPoolExecutor
^^^^^^^^^^^^^^^^^^

The :py:class:`concurrent.futures.ThreadPoolExecutor` is the default executor used due to its ease of setup. However, it is limited by the :ref:`GIL <python:threads>`. So while pickling of task arguments and return values are not required (as they are for :py:class:`concurrent.futures.ProcessPoolExecutor`), python code should not be expected to use more than one core at a time, even when multithreaded.

ProcessPoolExecutor
^^^^^^^^^^^^^^^^^^^

The :py:class:`concurrent.futures.ProcessPoolExecutor` is often the executor that gets uses in production. It is relatively easy to setup and use, although task arguments, return values, and exceptions must be pickle-able.

.. note::

   Some 3rd party libraries do not make their exceptions serializable and have to either be patched or have their exceptions caught in the task and re-raised with a serializable equivalent.

.. note::

   :py:class:`concurrent.futures.ProcessPoolExecutor` is not robust against seg faults. As soon as one worker crashes, the main process halts executing additional tasks and raises :py:exc:`concurrent.futures.process.BrokenProcessPool`.

CeleryExecutor
^^^^^^^^^^^^^^

An executor that uses celery to run tasks in workers either locally or distributed onto multiple computers. The celery executor does require that the celery workers be started before the terra app runs. This does require a little finesse, since typically terra decides what directories to mount. However, celery has its own mount table, and as long as its mounts include any possible mounts a task will need, :ref:`settings-path-translation` will adjust paths to refer to their new file names.

For example, if a service mounts ``/nfs/project1/date15/images`` to ``/images``, then a ``setting.image_file`` value of ``/data/project1/date15/images/img123.jpg`` will be translated to ``/images/img123.jpg`` in the service container. If the celery worker mounts ``/nfs/project1`` to ``/data`` then ``setting.image_file`` will become ``/data/date15/images/img123.jpg`` in the celery worker. While this all happens automatically and it not something you normally have to be aware of, you do need to be aware of this requirement when setting up mounts for celery workers.

.. _custom-executor:

Using custom executors
----------------------

To wrap your own executor up for terra, all you have to do is mix-in :py:class:`terra.executor.base.BaseExecutor` into your class. If the executor is multiprocess (on a single node) then ``multiprocess`` needs to be set to ``True`` for the class. For example: celery sets multiprocess to ``True`` because the :setting:`worker_pool` is defaulted to use prefork, which is multiprocess on a single node. (For example, if another distributed executor used threading to make multiple workers on each node ``multiprocess`` would be ``False``. It would also be ``False`` if there could only ever be one worker per computer. The fact that a worker process on one computer is a physically different process from a worker process on another computer has no bearing on the ``multiprocess`` setting.)

For workers like :py:class:`terra.executor.celery.executor.CeleryExecutor`, the worker is started before the terra app runs. These types of special workers outlive a single run of terra, and thus need a way to hook into the logger each time it changes. This is done by defining a ``configure_logger`` and ``reconfigure_logger`` method to connect to the correct logger for a task.
