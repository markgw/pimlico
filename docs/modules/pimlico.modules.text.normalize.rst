Normalize tokenized text
~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.normalize

+------------+--------------------------------+
| Path       | pimlico.modules.text.normalize |
+------------+--------------------------------+
| Executable | yes                            |
+------------+--------------------------------+

Perform text normalization on tokenized documents.

Currently, this includes only case normalization (to upper or lower case). In
the future, more normalization operations may be added.

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

+------+-------------------------------------------------------------------------------------------------------------------------+------------------------+
| Name | Description                                                                                                             | Type                   |
+======+=========================================================================================================================+========================+
| case | Transform all text to upper or lower case. Choose from 'upper' or 'lower', or leave blank to not perform transformation | 'upper', 'lower' or '' |
+------+-------------------------------------------------------------------------------------------------------------------------+------------------------+

