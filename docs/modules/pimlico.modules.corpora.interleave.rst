Interleaved corpora
~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.interleave

+------------+------------------------------------+
| Path       | pimlico.modules.corpora.interleave |
+------------+------------------------------------+
| Executable | no                                 |
+------------+------------------------------------+

Interleave data points from two (or more) corpora to produce a bigger corpus.

Similar to :mod:`~pimlico.modules.corpora.concat`, but interleaves the documents
when iterating. Preserves the order of documents within corpora and takes
documents two each corpus in inverse proportion to its length, i.e. spreads
out a smaller corpus so we don't finish iterating over it earlier than
the longer one.

They must have the same data point type, or one must be a subtype of the other.

In theory, we could find the most specific common ancestor and use that as the output type, but this is
not currently implemented and may not be worth the trouble. Perhaps we will add this in future.


This is a filter module. It is not executable, so won't appear in a pipeline's list of modules that can be run. It produces its output for the next module on the fly when the next module needs it.

Inputs
======

+---------+------------------------------------------------------------------------------------------------------------------------------------+
| Name    | Type(s)                                                                                                                            |
+=========+====================================================================================================================================+
| corpora | :class:`list <pimlico.datatypes.base.MultipleInputs>` of :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+---------+------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+--------+-----------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                       |
+========+===============================================================================================+
| corpus | :class:`grouped corpus with input doc type <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+-----------------------------------------------------------------------------------------------+

Options
=======

+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name             | Description                                                                                                                                     | Type   |
+==================+=================================================================================================================================================+========+
| archive_basename | Documents are regrouped into new archives. Base name to use for archive tar files. The archive number is appended to this. (Default: 'archive') | string |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| archive_size     | Documents are regrouped into new archives. Number of documents to include in each archive (default: 1k)                                         | string |
+------------------+-------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_interleave_module]
   type=pimlico.modules.corpora.interleave
   input_corpora=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_interleave_module]
   type=pimlico.modules.corpora.interleave
   input_corpora=module_a.some_output
   archive_basename=archive
   archive_size=1000

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-interleave.conf`