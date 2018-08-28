Archive grouper (filter)
~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.group

+------------+-------------------------------+
| Path       | pimlico.modules.corpora.group |
+------------+-------------------------------+
| Executable | no                            |
+------------+-------------------------------+

Group the data points (documents) of an iterable corpus into fixed-size archives.
This is a standard thing to do at the start of the pipeline, since it's a handy
way to store many (potentially small) files without running into filesystem problems.

The documents are simply grouped linearly into a series of groups (archives) such that
each (apart from the last) contains the given number of documents.

After grouping documents in this way, document map modules can be called on the corpus
and the grouping will be preserved as the corpus passes through the pipeline.

.. note::

   This module used to be called ``tar_filter``, but has been renamed in keeping
   with other changes in the new datatype system.

   There also used to be a ``tar`` module that wrote the grouped corpus to disk.
   This has now been removed, since most of the time it's fine to use this
   filter module instead. If you really want to store the grouped corpus, you
   can use the ``store`` module.


This is a filter module. It is not executable, so won't appear in a pipeline's list of modules that can be run. It produces its output for the next module on the fly when the next module needs it.

Inputs
======

+-----------+--------------------------------------------------------------------------+
| Name      | Type(s)                                                                  |
+===========+==========================================================================+
| documents | :class:`iterable_corpus <pimlico.datatypes.corpora.base.IterableCorpus>` |
+-----------+--------------------------------------------------------------------------+

Outputs
=======

+-----------+-----------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                       |
+===========+===============================================================================================+
| documents | :class:`grouped corpus with input doc type <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+-----------+-----------------------------------------------------------------------------------------------+

Options
=======

+------------------+------------------------------------------------------------------------------------------------------+--------+
| Name             | Description                                                                                          | Type   |
+==================+======================================================================================================+========+
| archive_size     | Number of documents to include in each archive (default: 1k)                                         | string |
+------------------+------------------------------------------------------------------------------------------------------+--------+
| archive_basename | Base name to use for archive tar files. The archive number is appended to this. (Default: 'archive') | string |
+------------------+------------------------------------------------------------------------------------------------------+--------+

