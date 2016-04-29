Stanford CoreNLP
~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corenlp

+------------+-------------------------+
| Path       | pimlico.modules.corenlp |
+------------+-------------------------+
| Executable | yes                     |
+------------+-------------------------+

Process documents one at a time with the `Stanford CoreNLP toolkit <http://stanfordnlp.github.io/CoreNLP/>`_.
CoreNLP provides a large number of NLP tools, including a POS-tagger, various parsers, named-entity recognition
and coreference resolution. Most of these tools can be run using this module.

The module uses the CoreNLP server to accept many inputs without the overhead of loading models.
If parallelizing, only a single CoreNLP server is run, since this is designed to set multiple Java threads running
if it receives multiple queries at the same time. Multiple Python processes send queries to the server and
process the output.

The module has no non-optional outputs, since what sort of output is available depends on the options you pass in:
that is, on which tools are run. Use the annotations option to choose which word annotations are added.
Otherwise, simply select the outputs that you want and the necessary tools will be run in the CoreNLP pipeline
to produce those outputs.

Currently, the module only accepts tokenized input. If pre-POS-tagged input is given, for example, the POS
tags won't be handed into CoreNLP. In the future, this will be implemented.

We also don't currently provide a way of choosing models other than the standard, pre-trained English models.
This is a small addition that will be implemented in the future.


Inputs
======

+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                                                                                                                                                         |
+===========+=================================================================================================================================================================================================================================+
| documents | :class:`WordAnnotationCorpus <pimlico.datatypes.word_annotations.WordAnnotationCorpus>` or :class:`TokenizedCorpus <pimlico.datatypes.tokenized.TokenizedCorpus>` or :class:`TarredCorpus <pimlico.datatypes.tar.TarredCorpus>` |
+-----------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

No non-optional outputs

Optional
--------

+-------------+------------------------------------------------------------------------------------------------+
| Name        | Type(s)                                                                                        |
+=============+================================================================================================+
| annotations | :class:`AnnotationFieldsFromOptions <pimlico.datatypes.word_annotations.WordAnnotationCorpus>` |
+-------------+------------------------------------------------------------------------------------------------+
| parse       | :class:`~pimlico.datatypes.parse.ConstituencyParseTreeCorpus`                                  |
+-------------+------------------------------------------------------------------------------------------------+
| parse-deps  | :class:`~pimlico.datatypes.parse.dependency.StanfordDependencyParseCorpus`                     |
+-------------+------------------------------------------------------------------------------------------------+
| dep-parse   | :class:`~pimlico.datatypes.parse.dependency.StanfordDependencyParseCorpus`                     |
+-------------+------------------------------------------------------------------------------------------------+
| raw         | :class:`~pimlico.datatypes.jsondoc.JsonDocumentCorpus`                                         |
+-------------+------------------------------------------------------------------------------------------------+
| coref       | :class:`~pimlico.datatypes.coref.corenlp.CorefCorpus`                                          |
+-------------+------------------------------------------------------------------------------------------------+

Options
=======

+------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| Name       | Description                                                                                                                                                                                                                         | Type                                            |
+============+=====================================================================================================================================================================================================================================+=================================================+
| annotators | Comma-separated list of word annotations to add, from CoreNLP's annotators. Choose from: word, pos, lemma, ner                                                                                                                      | string                                          |
+------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| dep_type   | Type of dependency parse to output, when outputting dependency parses, either from a constituency parse or direct dependency parse. Choose from the three types allowed by CoreNLP: 'basic', 'collapsed' or 'collapsed-ccprocessed' | 'basic', 'collapsed' or 'collapsed-ccprocessed' |
+------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| gzip       | If True, each output, except annotations, for each document is gzipped. This can help reduce the storage occupied by e.g. parser or coref output. Default: False                                                                    | bool                                            |
+------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| readable   | If True, JSON outputs are formatted in a readable fashion, pretty printed. Otherwise, they're as compact as possible. Default: False                                                                                                | bool                                            |
+------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+
| timeout    | Timeout for the CoreNLP server, which is applied to every job (document). Number of seconds. By default, we use the server's default timeout (15 secs), but you may want to increase this for more intensive tasks, like coref      | float                                           |
+------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+

