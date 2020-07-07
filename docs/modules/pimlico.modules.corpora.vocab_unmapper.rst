ID to tokenized corpus mapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.vocab_unmapper

+------------+----------------------------------------+
| Path       | pimlico.modules.corpora.vocab_unmapper |
+------------+----------------------------------------+
| Executable | yes                                    |
+------------+----------------------------------------+

Maps all the IDs in an integer lists corpus to their corresponding words
in a vocabulary, producing a tokenized textual corpus.

This is the inverse of :mod:`~pimlico.modules.corpora.vocab_mapper`, which
maps words to IDs. Typically, the resulting integer IDs are used for model
training, but sometimes we need to map in the opposite direction.


Inputs
======

+-------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name  | Type(s)                                                                                                                                                                 |
+=======+=========================================================================================================================================================================+
| ids   | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`IntegerListsDocumentType <pimlico.datatypes.corpora.ints.IntegerListsDocumentType>`> |
+-------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| vocab | :class:`dictionary <pimlico.datatypes.dictionary.Dictionary>`                                                                                                           |
+-------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                                |
+======+========================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+
| Name | Description                                                                                                                                                                        | Type   |
+======+====================================================================================================================================================================================+========+
| oov  | If given, assume the vocab_size+1 was used to represent out-of-vocabulary words and map this index to the given token. Special value 'skip' simply skips over vocab_size+1 indices | string |
+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_vocab_unmapper_module]
   type=pimlico.modules.corpora.vocab_unmapper
   input_ids=module_a.some_output
   input_vocab=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_vocab_unmapper_module]
   type=pimlico.modules.corpora.vocab_unmapper
   input_ids=module_a.some_output
   input_vocab=module_a.some_output
   oov=value

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-vocab_unmapper.conf`