Store a corpus
~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.store

+------------+-------------------------------+
| Path       | pimlico.modules.corpora.store |
+------------+-------------------------------+
| Executable | yes                           |
+------------+-------------------------------+

Store a corpus

Take documents from a corpus and write them to disk using the standard
writer for the corpus' data point type. This is
useful where documents are produced on the fly, for example from some filter
module or from an input reader, but where it is desirable to store the
produced corpus for further use, rather than always running the filters/readers
each time the corpus' documents are needed.


Inputs
======

+--------+------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                  |
+========+==========================================================================================+
| corpus | :class:`grouped_corpus<DataPointType> <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+------------------------------------------------------------------------------------------+

Outputs
=======

+--------+-----------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                       |
+========+===============================================================================================+
| corpus | :class:`grouped corpus with input doc type <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+-----------------------------------------------------------------------------------------------+

