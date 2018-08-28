Corpus statistics
~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.corpus_stats

+------------+--------------------------------------+
| Path       | pimlico.modules.corpora.corpus_stats |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

Some basic statistics about tokenized corpora

Counts the number of tokens, sentences and distinct tokens in a corpus.


Inputs
======

+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                                                                                |
+========+========================================================================================================================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+--------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-------+---------------------------------------------------------+
| Name  | Type(s)                                                 |
+=======+=========================================================+
| stats | :class:`named_file <pimlico.datatypes.files.NamedFile>` |
+-------+---------------------------------------------------------+

