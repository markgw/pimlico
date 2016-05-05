OpenNLP POS-tagger
~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.pos

+------------+-----------------------------+
| Path       | pimlico.modules.opennlp.pos |
+------------+-----------------------------+
| Executable | yes                         |
+------------+-----------------------------+

.. todo::

   Document this module


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
