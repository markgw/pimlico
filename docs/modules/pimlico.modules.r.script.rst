\!\! R script executor
~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.r.script

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+--------------------------+
| Path       | pimlico.modules.r.script |
+------------+--------------------------+
| Executable | yes                      |
+------------+--------------------------+

Simple interface to R that just involves running a given R script, first substituting in some paths from the
pipeline, making it easy to pass in data from the output of other modules.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+---------+--------------------------------------+
| Name    | Type(s)                              |
+=========+======================================+
| sources | **invalid input type specification** |
+---------+--------------------------------------+

Outputs
=======

+--------+---------------------------------------+
| Name   | Type(s)                               |
+========+=======================================+
| output | **invalid output type specification** |
+--------+---------------------------------------+

Options
=======

+--------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name   | Description                                                                                                                                                                                                                                                                                                                                                                                                           | Type   |
+========+=======================================================================================================================================================================================================================================================================================================================================================================================================================+========+
| script | (required) Path to the script to be run. The script itself may include substitutions of the form '{{inputX}}', which will be replaced with the absolute path to the data dir of the Xth input, and '{{output}}', which will be replaced with the absolute path to the output dir. The latter allows the script to output things other than the output file, which always exists and contains the full script's output | string |
+--------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_r_script_module]
   type=pimlico.modules.r.script
   input_sources=module_a.some_output
   script=value

