Corpus concatenation
~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.concat

+------------+--------------------------------+
| Path       | pimlico.modules.corpora.concat |
+------------+--------------------------------+
| Executable | no                             |
+------------+--------------------------------+

Concatenate two corpora to produce a bigger corpus.

They must have the same data point type, or one must be a subtype of the other.

In theory, we could find the most specific common ancestor and use that as the output type, but this is
not currently implemented and may not be worth the trouble. Perhaps we will add this in future.


This is a filter module. It is not executable, so won't appear in a pipeline's list of modules that can be run. It produces its output for the next module on the fly when the next module needs it.

Inputs
======

+---------+--------------------------------------------------------------------------------------------------------------------------+
| Name    | Type(s)                                                                                                                  |
+=========+==========================================================================================================================+
| corpora | :class:`list <pimlico.datatypes.base.MultipleInputs>` of :class:`IterableCorpus <pimlico.datatypes.base.IterableCorpus>` |
+---------+--------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+----------------------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                                  |
+========+==========================================================================================================+
| corpus | :class:`corpus with data-point from input <pimlico.modules.corpora.concat.info.DataPointTypeFromInputs>` |
+--------+----------------------------------------------------------------------------------------------------------+

