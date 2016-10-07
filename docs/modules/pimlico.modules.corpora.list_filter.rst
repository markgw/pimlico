Corpus document list filter
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.list_filter

+------------+-------------------------------------+
| Path       | pimlico.modules.corpora.list_filter |
+------------+-------------------------------------+
| Executable | yes                                 |
+------------+-------------------------------------+

Similar to :mod:pimlico.modules.corpora.split, but instead of taking a random split of the dataset, splits it
according to a given list of documents, putting those in the list in one set and the rest in another.


Inputs
======

+--------+------------------------------------------------------------+
| Name   | Type(s)                                                    |
+========+============================================================+
| corpus | :class:`TarredCorpus <pimlico.datatypes.tar.TarredCorpus>` |
+--------+------------------------------------------------------------+
| list   | :class:`StringList <pimlico.datatypes.base.StringList>`    |
+--------+------------------------------------------------------------+

Outputs
=======

+------+----------------------------------------------------------------------+
| Name | Type(s)                                                              |
+======+======================================================================+
| set1 | :class:`same as input corpus <pimlico.datatypes.base.TypeFromInput>` |
+------+----------------------------------------------------------------------+
| set2 | :class:`same as input corpus <pimlico.datatypes.base.TypeFromInput>` |
+------+----------------------------------------------------------------------+

