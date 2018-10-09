!! Annotated text to CoNLL dep parse input converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.malt.conll_parser_input

.. note::

   This module has not yet been updated to the new datatype system, so cannot be used in the `datatypes` branch. Soon it will be updated.

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

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_conll_parser_input_module]
   type=pimlico.modules.malt.conll_parser_input
   input_annotations=module_a.some_output
   

