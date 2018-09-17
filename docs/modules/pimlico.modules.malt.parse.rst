!! Malt dependency parser
~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.malt.parse

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+----------------------------+
| Path       | pimlico.modules.malt.parse |
+------------+----------------------------+
| Executable | yes                        |
+------------+----------------------------+

.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+-----------+--------------------------------------+
| Name      | Type(s)                              |
+===========+======================================+
| documents | **invalid input type specification** |
+-----------+--------------------------------------+

Outputs
=======

+--------+---------------------------------------+
| Name   | Type(s)                               |
+========+=======================================+
| parsed | **invalid output type specification** |
+--------+---------------------------------------+

Options
=======

+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name    | Description                                                                                                                                                                                              | Type   |
+=========+==========================================================================================================================================================================================================+========+
| model   | Filename of parsing model, or path to the file. If just a filename, assumed to be Malt models dir (models/malt). Default: engmalt.linear-1.7.mco, which can be acquired by 'make malt' in the models dir | string |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| no_gzip | By default, we gzip each document in the output data. If you don't do this, the output can get very large, since it's quite a verbose output format                                                      | bool   |
+---------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_malt_module]
   input_documents=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_malt_module]
   input_documents=module_a.some_output
   model=engmalt.linear-1.7.mco
   no_gzip=F

