OpenNLP POS-tagger
~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.pos

+------------+-----------------------------+
| Path       | pimlico.modules.opennlp.pos |
+------------+-----------------------------+
| Executable | yes                         |
+------------+-----------------------------+

Part-of-speech tagging using OpenNLP's tools.

By default, uses the pre-trained English model distributed with OpenNLP. If you want to use other models (e.g.
for other languages), download them from the OpenNLP website to the models dir (`models/opennlp`) and specify
the model name as an option.


Inputs
======

+------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                           |
+======+===================================================================================================================================================================+
| text | :class:`TokenizedCorpus <pimlico.datatypes.tokenized.TokenizedCorpus>` or :class:`WordAnnotationCorpus <pimlico.datatypes.word_annotations.WordAnnotationCorpus>` |
+------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-----------+---------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                               |
+===========+=======================================================================================+
| documents | :class:`AddAnnotationField <pimlico.datatypes.word_annotations.WordAnnotationCorpus>` |
+-----------+---------------------------------------------------------------------------------------+

Options
=======

+-------+----------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                            | Type   |
+=======+========================================================================================================================================+========+
| model | POS tagger model, full path or filename. If a filename is given, it is expected to be in the opennlp model directory (models/opennlp/) | string |
+-------+----------------------------------------------------------------------------------------------------------------------------------------+--------+

