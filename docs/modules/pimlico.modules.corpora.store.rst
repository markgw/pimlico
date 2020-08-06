Store a corpus
~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.store

+------------+-------------------------------+
| Path       | pimlico.modules.corpora.store |
+------------+-------------------------------+
| Executable | yes                           |
+------------+-------------------------------+

Store a corpus

Take documents from a corpus and write them to disk using the standard
writer for the corpus' data point type. This is
useful where documents are produced on the fly, for example from some filter
module or from an input reader, but where it is desirable to store the
produced corpus for further use, rather than always running the filters/readers
each time the corpus' documents are needed.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

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

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_store_module]
   type=pimlico.modules.corpora.store
   input_corpus=module_a.some_output
   

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-corpora-store.conf`
 * :ref:`test-config-corpora-filter_tokenize.conf`
 * :ref:`test-config-input-europarl.conf`
 * :ref:`test-config-input-raw_text_files.conf`
 * :ref:`test-config-core-filter_map.conf`

