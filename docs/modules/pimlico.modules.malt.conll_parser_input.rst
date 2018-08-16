Annotated text to CoNLL dep parse input converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.malt.conll_parser_input

+------------+-----------------------------------------+
| Path       | pimlico.modules.malt.conll_parser_input |
+------------+-----------------------------------------+
| Executable | yes                                     |
+------------+-----------------------------------------+

Converts word-annotations to CoNLL format, ready for input into the Malt parser.
Annotations must contain words and POS tags. If they contain lemmas, all the better; otherwise the word will
be repeated as the lemma.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+-------------+--------------------------------------+
| Name        | Type(s)                              |
+=============+======================================+
| annotations | **invalid input type specification** |
+-------------+--------------------------------------+

Outputs
=======

+------------+---------------------------------------+
| Name       | Type(s)                               |
+============+=======================================+
| conll_data | **invalid output type specification** |
+------------+---------------------------------------+

