\!\! Normalize raw text
~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.text_normalize

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+-------------------------------------+
| Path       | pimlico.modules.text.text_normalize |
+------------+-------------------------------------+
| Executable | yes                                 |
+------------+-------------------------------------+

Text normalization for raw text documents.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+--------+--------------------------------------+
| Name   | Type(s)                              |
+========+======================================+
| corpus | **invalid input type specification** |
+--------+--------------------------------------+

Outputs
=======

+--------+---------------------------------------+
| Name   | Type(s)                               |
+========+=======================================+
| corpus | **invalid output type specification** |
+--------+---------------------------------------+

Options
=======

+-------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| Name        | Description                                                                                                             | Type                   |
+=============+=========================================================================================================================+========================+
| case        | Transform all text to upper or lower case. Choose from 'upper' or 'lower', or leave blank to not perform transformation | 'upper', 'lower' or '' |
+-------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| blank_lines | Remove all blank lines (after whitespace stripping, if requested)                                                       | bool                   |
+-------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| strip       | Strip whitespace from the start and end of lines                                                                        | bool                   |
+-------------+-------------------------------------------------------------------------------------------------------------------------+------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_text_normalize_module]
   type=pimlico.modules.text.text_normalize
   input_corpus=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_text_normalize_module]
   type=pimlico.modules.text.text_normalize
   input_corpus=module_a.some_output
   case=
   blank_lines=T
   strip=T

