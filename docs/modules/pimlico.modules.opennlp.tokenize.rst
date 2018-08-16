OpenNLP tokenizer
~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.tokenize

+------------+----------------------------------+
| Path       | pimlico.modules.opennlp.tokenize |
+------------+----------------------------------+
| Executable | yes                              |
+------------+----------------------------------+

Sentence splitting and tokenization using OpenNLP's tools.

.. todo::

   Update to new datatypes system and add test pipeline


Inputs
======

+------+--------------------------------------+
| Name | Type(s)                              |
+======+======================================+
| text | **invalid input type specification** |
+------+--------------------------------------+

Outputs
=======

+-----------+---------------------------------------+
| Name      | Type(s)                               |
+===========+=======================================+
| documents | **invalid output type specification** |
+-----------+---------------------------------------+

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

