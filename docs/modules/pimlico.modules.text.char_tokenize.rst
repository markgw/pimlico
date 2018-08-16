Text to character level
~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.text.char_tokenize

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

