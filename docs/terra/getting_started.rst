=============
What is Terra
=============

Terra in an infrastructure with the purpose of running algorithms in a compute type agnostic way. The goal is, once an algorithm (app) is setup, the same algorithm can be deployed on multiple compute types

Getting Started
===============

Settings
--------

Everything in a terra app should be controlled by one main json file. This file will contain all the information from what compute type to use, any compute type settings, logging settings, input files, output, etc... Accessing the settings will be accomplished simply by

.. code-block:: python

  from terra import settings

  settings.my_settings
  settings.something.else.here

The settings file used is controlled by the environment variable ``TERRA_SETTINGS_FILE`` and is usually set by the cli.

While, underneath the hood the settings is a nested dictionary, it will be accessed via attributes instead of indexing, for ease of use.

.. rubric:: Templating

Default values of settings are prepopulated by :py:data:`terra.core.settings.global_templates`

.. rubric:: Advanced usage

