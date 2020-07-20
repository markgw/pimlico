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

This was difficult to do this efficiently for a large corpus using the
old tar storage format. There therefore used to be a strategy implemented
here where the input documents were read in linear order
and placed into a temporary set of small archives ("bins") and these were
concatenated into the larger archives, shuffling the documents in memory
in each during the process.

It is no longer necessary to do this, since the standard pipeline-internal
storage format permits efficient random access. However, it may sometimes
be necessary to use the linear-reading strategy: for example, if the input
comes from a filter module, its documents cannot be randomly accessed.

.. todo::

   Currently, this accepts any GroupedCorpus as input, but checks at runtime
   that the input is stored used the pipeline-internal format. It would be
   much better if this check could be enforced at the level of datatypes, so
   that the input datatype requirement explicitly rules out grouped corpora
   coming from input readers, filters or other dynamic sources.

   Since this requires some tricky changes to the datatype system, I'm not
   implementing it now, but it should be done in future.


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

+------------------+---------------------------------------------------------------------------------------------------+--------+
| Name             | Description                                                                                       | Type   |
+==================+===================================================================================================+========+
| archive_basename | Basename to use for archives in the output corpus. Default: 'archive'                             | string |
+------------------+---------------------------------------------------------------------------------------------------+--------+
| seed             | Seed for the random number generator. The RNG is always seeded, for reproducibility. Default: 999 | int    |
+------------------+---------------------------------------------------------------------------------------------------+--------+

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
   archive_basename=archive
   seed=999

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-corpora-shuffle.conf`