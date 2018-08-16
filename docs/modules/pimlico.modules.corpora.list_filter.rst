Corpus document list filter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.list_filter

+------------+-------------------------------------+
| Path       | pimlico.modules.corpora.list_filter |
+------------+-------------------------------------+
| Executable | yes                                 |
+------------+-------------------------------------+

Similar to :mod:`~pimlico.modules.corpora.split`, but instead of taking a random split of the dataset, splits it
according to a given list of documents, putting those in the list in one set and the rest in another.


Inputs
======

+--------+------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                  |
+========+==========================================================================================+
| corpus | :class:`grouped_corpus<DataPointType> <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+------------------------------------------------------------------------------------------+
| list   | :class:`string_list <pimlico.datatypes.core.StringList>`                                 |
+--------+------------------------------------------------------------------------------------------+

Outputs
=======

+------+-----------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                       |
+======+===============================================================================================+
| set1 | :class:`grouped corpus with input doc type <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+------+-----------------------------------------------------------------------------------------------+
| set2 | :class:`grouped corpus with input doc type <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+------+-----------------------------------------------------------------------------------------------+

