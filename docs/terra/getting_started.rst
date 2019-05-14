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

.. rubric:: Templating

Default values of settings are prepopulated by :py:data:`terra.core.settings.global_templates`. This data structure is a list of tuple pair of :class:`dict`. Within the pair, the first :class:`dict` represents a *pattern*, and the second is the *default* values. When values of *pattern* match the configuration, then the *defaults* of that pattern are applied. These *defaults* are applied in order, where the last *default* overrides the earlier ones, but by combining all of the dictionaries into one, using :func:`vsi.tools.python.nested_update`

.. rubric:: Advanced usage

Todo