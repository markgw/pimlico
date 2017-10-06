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

+--------+-------------------------------------+
| Name   | Type(s)                             |
+========+=====================================+
| corpus | TarredCorpus<TokenizedDocumentType> |
+--------+-------------------------------------+

Outputs
=======

+-------+--------------------------------------------+
| Name  | Type(s)                                    |
+=======+============================================+
| stats | :func:`~pimlico.datatypes.files.NamedFile` |
+-------+--------------------------------------------+

