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

+--------+--------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                          |
+========+==================================================================================================+
| corpus | :class:`grouped_corpus<TokenizedDocumentType> <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+--------------------------------------------------------------------------------------------------+

Outputs
=======

+-------+----------------------------------------------------------+
| Name  | Type(s)                                                  |
+=======+==========================================================+
| stats | :class:`~pimlico.datatypes.files.NamedFile <named_file>` |
+-------+----------------------------------------------------------+

