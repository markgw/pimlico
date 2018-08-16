Corpus concatenation
~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.concat

+------------+--------------------------------+
| Path       | pimlico.modules.corpora.concat |
+------------+--------------------------------+
| Executable | no                             |
+------------+--------------------------------+

Concatenate two (or more) corpora to produce a bigger corpus.

They must have the same data point type, or one must be a subtype of the other.


This is a filter module. It is not executable, so won't appear in a pipeline's list of modules that can be run. It produces its output for the next module on the fly when the next module needs it.

Inputs
======

+---------+--------------------------------------------------------------------------------------------------------------------------------------------------+
| Name    | Type(s)                                                                                                                                          |
+=========+==================================================================================================================================================+
| corpora | :class:`list <pimlico.datatypes.base.MultipleInputs>` of :class:`iterable_corpus<DataPointType> <pimlico.datatypes.corpora.base.IterableCorpus>` |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+--------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                |
+========+========================================================================================================+
| corpus | :class:`corpus with data-point from input <pimlico.datatypes.corpora.grouped.CorpusWithTypeFromInput>` |
+--------+--------------------------------------------------------------------------------------------------------+

