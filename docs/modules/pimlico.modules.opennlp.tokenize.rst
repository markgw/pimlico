OpenNLP tokenizer
~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.tokenize

+------------+----------------------------------+
| Path       | pimlico.modules.opennlp.tokenize |
+------------+----------------------------------+
| Executable | yes                              |
+------------+----------------------------------+

Sentence splitting and tokenization using OpenNLP's tools.


Inputs
======

+------+-----------------------------------+
| Name | Type(s)                           |
+======+===================================+
| text | TarredCorpus<RawTextDocumentType> |
+------+-----------------------------------+

Outputs
=======

+-----------+-------------------------------------------------------+
| Name      | Type(s)                                               |
+===========+=======================================================+
| documents | :class:`~pimlico.datatypes.tokenized.TokenizedCorpus` |
+-----------+-------------------------------------------------------+

Options
=======

+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name           | Description                                                                                                                                                        | Type   |
+================+====================================================================================================================================================================+========+
| token_model    | Tokenization model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/)          | string |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| tokenize_only  | By default, sentence splitting is performed prior to tokenization. If tokenize_only is set, only the tokenization step is executed                                 | bool   |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| sentence_model | Sentence segmentation model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/) | string |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

