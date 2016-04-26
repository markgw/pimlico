Pimlico module: Annotated text to CoNLL dep parse input converter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.malt.conll_parser_input

+------------+-----------------------------------------+
| Path       | pimlico.modules.malt.conll_parser_input |
+------------+-----------------------------------------+
| Executable | yes                                     |
+------------+-----------------------------------------+

Converts word-annotations to CoNLL format, ready for input into the Malt parser.
Annotations must contain words and POS tags. If they contain lemmas, all the better; otherwise the word will
be repeated as the lemma.


Inputs
======

+-------------+----------------------------------------------------------------------------------------------------------------------+
| Name        | Type(s)                                                                                                              |
+=============+======================================================================================================================+
| annotations | :class:`WordAnnotationCorpus <pimlico.datatypes.word_annotations.WordAnnotationCorpus>` with 'word' and 'pos' fields |
+-------------+----------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+------------+---------------------------------------------------------------------------------------------------------------+
| Name       | Type(s)                                                                                                       |
+============+===============================================================================================================+
| conll_data | :class:`CoNLLDependencyParseInputCorpus <pimlico.datatypes.parse.dependency.CoNLLDependencyParseInputCorpus>` |
+------------+---------------------------------------------------------------------------------------------------------------+

