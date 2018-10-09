Tokenized corpus to ID mapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.vocab_mapper

+------------+--------------------------------------+
| Path       | pimlico.modules.corpora.vocab_mapper |
+------------+--------------------------------------+
| Executable | yes                                  |
+------------+--------------------------------------+

.. todo::

   Write description of vocab mapper module

.. todo::

   Add test pipeline and test


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

