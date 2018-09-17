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

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_corpus_stats_module]
   input_corpus=module_a.some_output
   

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`:

 * :ref:`test-config-stats.conf`