\!\! Term\-feature matrix builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.features.term_feature_matrix_builder

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+------------------------------------------------------+
| Path       | pimlico.modules.features.term_feature_matrix_builder |
+------------+------------------------------------------------------+
| Executable | yes                                                  |
+------------+------------------------------------------------------+

.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+------+--------------------------------------+
| Name | Type(s)                              |
+======+======================================+
| data | **invalid input type specification** |
+------+--------------------------------------+

Outputs
=======

+--------+---------------------------------------+
| Name   | Type(s)                               |
+========+=======================================+
| matrix | **invalid output type specification** |
+--------+---------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_term_feature_matrix_builder_module]
   type=pimlico.modules.features.term_feature_matrix_builder
   input_data=module_a.some_output
   

