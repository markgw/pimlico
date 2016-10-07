OpenNLP coreference resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.opennlp.coreference_pipeline

+------------+----------------------------------------------+
| Path       | pimlico.modules.opennlp.coreference_pipeline |
+------------+----------------------------------------------+
| Executable | yes                                          |
+------------+----------------------------------------------+

Runs the full coreference resolution pipeline using OpenNLP. This includes sentence splitting, tokenization,
pos tagging, parsing and coreference resolution. The results of all the stages are available in the output.

Use local config setting opennlp_memory to set the limit on Java heap memory for the OpenNLP processes. If
parallelizing, this limit is shared between the processes. That is, each OpenNLP worker will have a memory
limit of `opennlp_memory / processes`. That setting can use `g`, `G`, `m`, `M`, `k` and `K`, as in the Java setting.


Inputs
======

+------+-----------------------------------+
| Name | Type(s)                           |
+======+===================================+
| text | TarredCorpus<RawTextDocumentType> |
+------+-----------------------------------+

Outputs
=======

+-------+-------------------------------------------------------+
| Name  | Type(s)                                               |
+=======+=======================================================+
| coref | :class:`~pimlico.datatypes.coref.opennlp.CorefCorpus` |
+-------+-------------------------------------------------------+


Optional
--------

+-----------+--------------------------------------------------------------------------+
| Name      | Type(s)                                                                  |
+===========+==========================================================================+
| tokenized | :class:`~pimlico.datatypes.tokenized.TokenizedCorpus`                    |
+-----------+--------------------------------------------------------------------------+
| pos       | :class:`~pimlico.datatypes.word_annotations.WordAnnotationCorpusWithPos` |
+-----------+--------------------------------------------------------------------------+
| parse     | :class:`~pimlico.datatypes.parse.ConstituencyParseTreeCorpus`            |
+-----------+--------------------------------------------------------------------------+

Options
=======

+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name           | Description                                                                                                                                                                                                               | Type   |
+================+===========================================================================================================================================================================================================================+========+
| gzip           | If True, each output, except annotations, for each document is gzipped. This can help reduce the storage occupied by e.g. parser or coref output. Default: False                                                          | bool   |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| token_model    | Tokenization model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/)                                                                 | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| parse_model    | Parser model, full path or directory name. If a filename is given, it is expected to be in the OpenNLP model directory (models/opennlp/)                                                                                  | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| timeout        | Timeout in seconds for each individual coref resolution task. If this is exceeded, an InvalidDocument is returned for that document                                                                                       | int    |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| coref_model    | Coreference resolution model, full path or directory name. If a filename is given, it is expected to be in the OpenNLP model directory (models/opennlp/). Default: '' (standard English opennlp model in models/opennlp/) | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| readable       | If True, pretty-print the JSON output, so it's human-readable. Default: False                                                                                                                                             | bool   |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| pos_model      | POS tagger model, full path or filename. If a filename is given, it is expected to be in the opennlp model directory (models/opennlp/)                                                                                    | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| sentence_model | Sentence segmentation model. Specify a full path, or just a filename. If a filename is given it is expected to be in the opennlp model directory (models/opennlp/)                                                        | string |
+----------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

