POS\-tagger
~~~~~~~~~~~

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

+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                                |
+======+========================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                                                   |
+======+===========================================================================================================================================================================================+
| pos  | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`WordAnnotationsDocumentType <pimlico.datatypes.corpora.word_annotations.WordAnnotationsDocumentType>`> |
+------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+-------+----------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                            | Type   |
+=======+========================================================================================================================================+========+
| model | POS tagger model, full path or filename. If a filename is given, it is expected to be in the opennlp model directory (models/opennlp/) | string |
+-------+----------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_opennlp_pos_tagger_module]
   type=pimlico.modules.opennlp.pos
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_opennlp_pos_tagger_module]
   type=pimlico.modules.opennlp.pos
   input_text=module_a.some_output
   model=en-pos-maxent.bin

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-opennlp-pos.conf`

