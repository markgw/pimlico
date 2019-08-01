Random shuffle
~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.shuffle

+------------+---------------------------------+
| Path       | pimlico.modules.corpora.shuffle |
+------------+---------------------------------+
| Executable | yes                             |
+------------+---------------------------------+

Randomly shuffles all the documents in a grouped corpus, outputting
them to a new set of archives with the same sizes as the input archives.

It is difficult to do this efficiently for a large corpus.
We use a strategy where the input documents are read in linear order
and placed into a temporary set of small archives ("bins"). Then these are
concatenated into the larger archives, shuffling the documents in memory
in each during the process.

The expected average size of the temporary bins can be set using the
``bin_size`` parameter. Alternatively, the exact total number of
bins to use can be set using the ``num_bins`` parameter.

It may be necessary to lower the bin size if, for example, your
individual documents are very large files. You might also find the
process is noticeably faster with a higher bin size if your files
are small.


Inputs
======

+--------+---------------------------------------------------------------------------+
| Name   | Type(s)                                                                   |
+========+===========================================================================+
| corpus | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+---------------------------------------------------------------------------+

Outputs
=======

+--------+-----------------------------------------------------------------------------------------------+
| Name   | Type(s)                                                                                       |
+========+===============================================================================================+
| corpus | :class:`grouped corpus with input doc type <pimlico.datatypes.corpora.grouped.GroupedCorpus>` |
+--------+-----------------------------------------------------------------------------------------------+

Options
=======

+--------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name               | Description                                                                                                                                                                                                                                                                                                                | Type   |
+====================+============================================================================================================================================================================================================================================================================================================================+========+
| keep_archive_names | By default, it is assumed that all doc names are unique to the whole corpus, so the same doc names are used once the documents are put into their new archives. If doc names are only unique within the input archives, use this and the input archive names will be included in the output document names. Default: False | bool   |
+--------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| archive_basename   | Basename to use for archives in the output corpus. Default: 'archive'                                                                                                                                                                                                                                                      | string |
+--------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| num_bins           | Directly set the number of temporary bins to put document into. If set, bin_size is ignored                                                                                                                                                                                                                                | int    |
+--------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| bin_size           | Target expected size of temporary bins into which documents are shuffled. The actual size may vary, but they will on average have this size. Default: 100                                                                                                                                                                  | int    |
+--------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_shuffle_module]
   type=pimlico.modules.corpora.shuffle
   input_corpus=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_shuffle_module]
   type=pimlico.modules.corpora.shuffle
   input_corpus=module_a.some_output
   keep_archive_names=F
   archive_basename=archive
   num_bins=0
   bin_size=100

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-shuffle.conf`