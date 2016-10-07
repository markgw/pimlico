OpenNLP NER
~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.ner

+------------+-----------------------------+
| Path       | pimlico.modules.opennlp.ner |
+------------+-----------------------------+
| Executable | yes                         |
+------------+-----------------------------+

Named-entity recognition using OpenNLP's tools.

By default, uses the pre-trained English model distributed with OpenNLP. If you want to use other models (e.g.
for other languages), download them from the OpenNLP website to the models dir (`models/opennlp`) and specify
the model name as an option.

Note that the default model is for identifying person names only. You can identify other name types by loading
other pre-trained OpenNLP NER models. Identification of multiple name types at the same time is not (yet)
implemented.


Inputs
======

+------+-----------------------------------------------------------------+
| Name | Type(s)                                                         |
+======+=================================================================+
| text | TarredCorpus<TokenizedDocumentType|WordAnnotationsDocumentType> |
+------+-----------------------------------------------------------------+

Outputs
=======

+-----------+-------------------------------------------------------+
| Name      | Type(s)                                               |
+===========+=======================================================+
| documents | :class:`~pimlico.datatypes.spans.SentenceSpansCorpus` |
+-----------+-------------------------------------------------------+

Options
=======

+-------+---------------------------------------------------------------------------------------------------------------------------------+--------+
| Name  | Description                                                                                                                     | Type   |
+=======+=================================================================================================================================+========+
| model | NER model, full path or filename. If a filename is given, it is expected to be in the opennlp model directory (models/opennlp/) | string |
+-------+---------------------------------------------------------------------------------------------------------------------------------+--------+

