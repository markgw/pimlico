Corpus subset
~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.subset

+------------+--------------------------------+
| Path       | pimlico.modules.corpora.subset |
+------------+--------------------------------+
| Executable | no                             |
+------------+--------------------------------+

Simple filter to truncate a dataset after a given number of documents, potentially offsetting by a number
of documents. Mainly useful for creating small subsets of a corpus for testing a pipeline before running
on the full corpus.


This is a filter module. It is not executable, so won't appear in a pipeline's list of modules that can be run. It produces its output for the next module on the fly when the next module needs it.

Inputs
======

+-----------+-----------------------------------------------------------------+
| Name      | Type(s)                                                         |
+===========+=================================================================+
| documents | :class:`IterableCorpus <pimlico.datatypes.base.IterableCorpus>` |
+-----------+-----------------------------------------------------------------+

Outputs
=======

+-----------+------------------------------------------------------------------+
| Name      | Type(s)                                                          |
+===========+==================================================================+
| documents | :class:`~pimlico.modules.corpora.subset.info.CorpusSubsetFilter` |
+-----------+------------------------------------------------------------------+

Options
=======

+--------+---------------------------------------------------------------------------------------------+------+
| Name   | Description                                                                                 | Type |
+========+=============================================================================================+======+
| offset | Number of documents to skip at the beginning of the corpus (default: 0, start at beginning) | int  |
+--------+---------------------------------------------------------------------------------------------+------+
| size   | (required)                                                                                  | int  |
+--------+---------------------------------------------------------------------------------------------+------+

