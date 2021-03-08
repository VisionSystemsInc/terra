=============
What is Terra
=============

Terra in an infrastructure with the purpose of running algorithms in a compute architecture agnostic way. The goal is, once an algorithm (app) is setup, the same algorithm can be deployed on multiple compute arches

Getting Started
===============

Settings
--------

Everything in a terra app should be controlled by one main json file. This file will contain all the information from what compute arch to use, any compute arch settings, logging settings, input files, output, etc... Accessing the settings will be accomplished simply by

.. code-block:: python

  from terra import settings

  settings.my_settings
  settings.something.else.here

The settings file used is controlled by the environment variable :envvar:`TERRA_SETTINGS_FILE` and is usually set by the cli.

While, underneath the hood the settings is a nested dictionary, it will be accessed via attributes instead of indexing, for ease of use.

Templating
^^^^^^^^^^

Default values of settings are prepopulated by :py:data:`terra.core.settings.global_templates`. This data structure is a list of tuple pair of :class:`dict`. Within the pair, the first :class:`dict` represents a *pattern*, and the second is the *default* values. When values of *pattern* match the configuration, then the *defaults* of that pattern are applied. These *defaults* are applied in order, where the last *default* overrides the earlier ones, but by combining all of the dictionaries into one, using :func:`vsi.tools.python.nested_update`

.. _settings-path-translation:

Path translation
^^^^^^^^^^^^^^^^

Since services and tasks can run in different containers or even on different computers, terra settings has a "path translation" feature built in. If any settings name ends in ``_dir``/``_dirs``/``_file``/``_files``/``_path``/``paths``, then terra will automatically convert the paths between containers, e.g. ``settings.foo.bar_path``. This is done my inspecting the compute's configuration and creating a mount map. If ``/opt/test/foo`` is mounted to ``/data`` in a container, then if ``bar_path`` is set to ``/opt/test/foo/bar/file.txt``, on the other container/computer, it will have the value ``/data/bar/file.txt``. For computes that utilize the environment variables ``TERRA_*_VOLUMES``, these will be included in the volume mapping.

For tasks, keyword arguments are also translated, if their names end with the same suffixes. This includes the keyword arguments themselves, and any nested combination of list/tuple/dict that has a dict key value ending with the same suffixes.

If the return value of a task is also a nested list/tuple/dict, those keys ending with the same suffixes are also translated back.

When a compute/executor has the potential to change paths, a ``configuration_map_service``/``configuration_map`` method is needed to return this list of tuple pairs (host, container) of mounts mounts.

Advanced usage
^^^^^^^^^^^^^^

Todo