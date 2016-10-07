Tar archive grouper (filter)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.tar_filter

+------------+------------------------------------+
| Path       | pimlico.modules.corpora.tar_filter |
+------------+------------------------------------+
| Executable | no                                 |
+------------+------------------------------------+

Like :mod:`tar <pimlico.modules.corpora.tar>`, but doesn't write the archives to disk. Instead simulates the behaviour of
tar but as a filter, grouping files on the fly and passing them through with an archive name


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

+-----------+---------------------------------------------------------------------------------+
| Name      | Type(s)                                                                         |
+===========+=================================================================================+
| documents | :class:`tarred corpus with input doc type <pimlico.datatypes.tar.TarredCorpus>` |
+-----------+---------------------------------------------------------------------------------+

Options
=======

+------------------+------------------------------------------------------------------------------------------------------+--------+
| Name             | Description                                                                                          | Type   |
+==================+======================================================================================================+========+
| archive_size     | Number of documents to include in each archive (default: 1k)                                         | string |
+------------------+------------------------------------------------------------------------------------------------------+--------+
| archive_basename | Base name to use for archive tar files. The archive number is appended to this. (Default: 'archive') | string |
+------------------+------------------------------------------------------------------------------------------------------+--------+

