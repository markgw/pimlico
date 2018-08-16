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

Can be run on an iterable corpus or a tarred corpus. If the input is a tarred corpus, the filter will
emulate a tarred corpus with the appropriate datatype, passing through the archive names from the input.

When a number of valid documents is required (calculating corpus length when skipping invalid docs),
if one is stored in the metadata as ``valid_documents``, that count is used instead of iterating
over the data to count them up.


This is a filter module. It is not executable, so won't appear in a pipeline's list of modules that can be run. It produces its output for the next module on the fly when the next module needs it.

Inputs
======

+--------+-----------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                 |
+========+=========================================================================================+
| corpus | :class:`iterable_corpus<DataPointType> <pimlico.datatypes.corpora.base.IterableCorpus>` |
+--------+-----------------------------------------------------------------------------------------+

Outputs
=======

+--------+--------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                |
+========+========================================================================================================+
| corpus | :class:`corpus with data-point from input <pimlico.datatypes.corpora.grouped.CorpusWithTypeFromInput>` |
+--------+--------------------------------------------------------------------------------------------------------+

Options
=======

+--------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------+
| Name         | Description                                                                                                                                                                                                                                  | Type |
+==============+==============================================================================================================================================================================================================================================+======+
| offset       | Number of documents to skip at the beginning of the corpus (default: 0, start at beginning)                                                                                                                                                  | int  |
+--------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------+
| skip_invalid | Skip over any invalid documents so that the output subset contains the chosen number of (valid) documents (or as many as possible) and no invalid ones. By default, invalid documents are passed through and counted towards the subset size | bool |
+--------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------+
| size         | (required) Number of documents to include                                                                                                                                                                                                    | int  |
+--------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+------+

