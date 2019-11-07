
.. _settings:

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
