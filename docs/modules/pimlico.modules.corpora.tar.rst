Pimlico module: Tar archive grouper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.tar

+------------+-----------------------------+
| Path       | pimlico.modules.corpora.tar |
+------------+-----------------------------+
| Executable | yes                         |
+------------+-----------------------------+

Group the files of a multi-file iterable corpus into tar archives. This is a
standard thing to do at the start of the pipeline, since it's a handy way to
store many (potentially small) files without running into filesystem problems.

The files are simply grouped linearly into a series of tar archives such that
each (apart from the last) contains the given number.

After grouping documents in this way, document map modules can be called on the corpus and the
grouping will be preserved as the corpus passes through the pipeline.


Inputs
======

+-----------+-----------------------------------------------------------------+
| Name      | Type(s)                                                         |
+===========+=================================================================+
| documents | :class:`IterableCorpus <pimlico.datatypes.base.IterableCorpus>` |
+-----------+-----------------------------------------------------------------+

Outputs
=======

+-----------+------------------------------------------------------------+
| Name      | Type(s)                                                    |
+===========+============================================================+
| documents | :class:`TarredCorpus <pimlico.datatypes.tar.TarredCorpus>` |
+-----------+------------------------------------------------------------+

Options
=======

+------------------+------------------------------------------------------------------------------------------------------+--------+
| Name             | Description                                                                                          | Type   |
+==================+======================================================================================================+========+
| archive_basename | Base name to use for archive tar files. The archive number is appended to this. (Default: 'archive') | string |
+------------------+------------------------------------------------------------------------------------------------------+--------+
| archive_size     | Number of documents to include in each archive (default: 1k)                                         | string |
+------------------+------------------------------------------------------------------------------------------------------+--------+

