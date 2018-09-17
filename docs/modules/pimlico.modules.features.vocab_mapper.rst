!! Term-feature corpus vocab mapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.features.vocab_mapper

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+---------------------------------------+
| Path       | pimlico.modules.features.vocab_mapper |
+------------+---------------------------------------+
| Executable | yes                                   |
+------------+---------------------------------------+

.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+---------------+--------------------------------------+
| Name          | Type(s)                              |
+===============+======================================+
| data          | **invalid input type specification** |
+---------------+--------------------------------------+
| term_vocab    | **invalid input type specification** |
+---------------+--------------------------------------+
| feature_vocab | **invalid input type specification** |
+---------------+--------------------------------------+

Outputs
=======

+------+---------------------------------------+
| Name | Type(s)                               |
+======+=======================================+
| data | **invalid output type specification** |
+------+---------------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_term_feature_vocab_mapper_module]
   input_data=module_a.some_output
   input_term_vocab=module_a.some_output
   input_feature_vocab=module_a.some_output
   

