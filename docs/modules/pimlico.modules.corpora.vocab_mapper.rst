Tokenized corpus to ID mapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.vocab_mapper

+------------+--------------------------------------+
| Path       | pimlico.modules.corpora.vocab_mapper |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

Maps all the words in a tokenized textual corpus to integer IDs, storing
just lists of integers in the output.

This is typically done before doing things like training models on textual
corpora. It ensures that a consistent mapping from words to IDs is used
throughout the pipeline. The training modules use this pre-mapped form
of input, instead of performing the mapping as they read the data, because
it is much more efficient if the corpus needs to be iterated over many times,
as is typical in model training.

First use the :mod:`~pimlico.modules.corpora.vocab_builder` module to
construct the word-ID mapping and filter the vocabulary as you wish,
then use this module to apply the mapping to the corpus.


Inputs
======

+-------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name  | Type(s)                                                                                                                                                                |
+=======+========================================================================================================================================================================+
| text  | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+-------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| vocab | :class:`dictionary <pimlico.datatypes.dictionary.Dictionary>`                                                                                                          |
+-------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                                 |
+======+=========================================================================================================================================================================+
| ids  | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`IntegerListsDocumentType <pimlico.datatypes.corpora.ints.IntegerListsDocumentType>`> |
+------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Options
=======

+------+-------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name | Description                                                                                                                               | Type   |
+======+===========================================================================================================================================+========+
| oov  | If given, special token to map all OOV tokens to. Otherwise, use vocab_size+1 as index. Special value 'skip' simply skips over OOV tokens | string |
+------+-------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_vocab_mapper_module]
   type=pimlico.modules.corpora.vocab_mapper
   input_text=module_a.some_output
   input_vocab=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_vocab_mapper_module]
   type=pimlico.modules.corpora.vocab_mapper
   input_text=module_a.some_output
   input_vocab=module_a.some_output
   oov=value

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-vocab_mapper.conf`