!! OpenNLP constituency parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.parse

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-------------------------------+
| Path       | pimlico.modules.opennlp.parse |
+------------+-------------------------------+
| Executable | yes                           |
+------------+-------------------------------+

.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+-----------+------------------------------------------------------------------------------+
| Name      | Type(s)                                                                      |
+===========+==============================================================================+
| documents | **invalid input type specification** or **invalid input type specification** |
+-----------+------------------------------------------------------------------------------+

Outputs
=======

+--------+---------------------------------------+
| Name   | Type(s)                               |
+========+=======================================+
| parser | **invalid output type specification** |
+--------+---------------------------------------+

Options
=======

+-------+------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                              | Type   |
+=======+==========================================================================================================================================+========+
| model | Parser model, full path or directory name. If a filename is given, it is expected to be in the OpenNLP model directory (models/opennlp/) | string |
+-------+------------------------------------------------------------------------------------------------------------------------------------------+--------+

