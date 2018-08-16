!! Tokenized corpus to ID mapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.vocab_mapper

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+--------------------------------------+
| Path       | pimlico.modules.corpora.vocab_mapper |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

.. todo::

   Write description of vocab mapper module

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+-------+--------------------------------------+
| Name  | Type(s)                              |
+=======+======================================+
| text  | **invalid input type specification** |
+-------+--------------------------------------+
| vocab | **invalid input type specification** |
+-------+--------------------------------------+

Outputs
=======

+------+---------------------------------------+
| Name | Type(s)                               |
+======+=======================================+
| ids  | **invalid output type specification** |
+------+---------------------------------------+

Options
=======

+------+-------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name | Description                                                                                                                               | Type   |
+======+===========================================================================================================================================+========+
| oov  | If given, special token to map all OOV tokens to. Otherwise, use vocab_size+1 as index. Special value 'skip' simply skips over OOV tokens | string |
+------+-------------------------------------------------------------------------------------------------------------------------------------------+--------+

