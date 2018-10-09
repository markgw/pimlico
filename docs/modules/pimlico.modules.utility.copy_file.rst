!! Copy file
~~~~~~~~~~~~

.. py:module:: pimlico.modules.utility.copy_file

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-----------------------------------+
| Path       | pimlico.modules.utility.copy_file |
+------------+-----------------------------------+
| Executable | yes                               |
+------------+-----------------------------------+

Copy a file

Simple utility for copying a file (which presumably comes from the output of another module) into a particular
location. Useful for collecting together final output at the end of a pipeline.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+--------+--------------------------------------+
| Name   | Type(s)                              |
+========+======================================+
| source | **invalid input type specification** |
+--------+--------------------------------------+

Outputs
=======

No outputs
Options
=======

+-------------+---------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name        | Description                                                                                                                                 | Type   |
+=============+=============================================================================================================================================+========+
| target_name | Name to rename the target file to. If not given, it will have the same name as the source file. Ignored if there's more than one input file | string |
+-------------+---------------------------------------------------------------------------------------------------------------------------------------------+--------+
| target_dir  | (required) Path to directory into which the file should be copied. Will be created if it doesn't exist                                      | string |
+-------------+---------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_copy_file_module]
   type=pimlico.modules.utility.copy_file
   input_source=module_a.some_output
   target_dir=value

This example usage includes more options.

.. code-block:: ini
   
   [my_copy_file_module]
   type=pimlico.modules.utility.copy_file
   input_source=module_a.some_output
   target_name=value
   target_dir=value

