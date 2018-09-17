!! Text to character level
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.char_tokenize

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

+------------+------------------------------------+
| Path       | pimlico.modules.text.char_tokenize |
+------------+------------------------------------+
| Executable | yes                                |
+------------+------------------------------------+

Filter to treat text data as character-level tokenized data. This makes it simple to
train character-level models, since the output appears exactly like a tokenized
document, where each token is a single character. You can then feed it into any
module that expects tokenized text.

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

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_char_tokenize_module]
   input_corpus=module_a.some_output
   

