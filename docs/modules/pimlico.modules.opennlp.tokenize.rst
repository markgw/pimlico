Tokenizer
~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.tokenize

+------------+----------------------------------+
| Path       | pimlico.modules.opennlp.tokenize |
+------------+----------------------------------+
| Executable | yes                              |
+------------+----------------------------------+

Sentence splitting and tokenization using OpenNLP's tools.

Sentence splitting may be skipped by setting the option `tokenize_only=T`. The tokenizer
will then assume that each line in the input file represents a sentence and tokenize
within the lines.

.. todo:

   The OpenNLP tokenizer test pipeline needs models to have been installed before running.
   Once `automatic fetching of models/data <https://github.com/markgw/pimlico/issues/9>`_
   has been implemented, use this for the models and move the test pipeline to the main suite.


Inputs
======

+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                        |
+======+================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TextDocumentType <pimlico.datatypes.corpora.data_points.TextDocumentType>`> |
+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                                                                                                |
+===========+========================================================================================================================================================================+
| documents | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name           | Description                                                                                                                                                        | Type   |
+================+====================================================================================================================================================================+========+
| sentence_model | Sentence segmentation model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/) | string |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| token_model    | Tokenization model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/)          | string |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| tokenize_only  | By default, sentence splitting is performed prior to tokenization. If tokenize_only is set, only the tokenization step is executed                                 | bool   |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_opennlp_tokenizer_module]
   type=pimlico.modules.opennlp.tokenize
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_opennlp_tokenizer_module]
   type=pimlico.modules.opennlp.tokenize
   input_text=module_a.some_output
   sentence_model=en-sent.bin
   token_model=en-token.bin
   tokenize_only=F

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-opennlp-tokenize.conf`

