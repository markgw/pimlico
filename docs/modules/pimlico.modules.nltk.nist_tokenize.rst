NIST tokenizer
~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.nltk.nist_tokenize

+------------+------------------------------------+
| Path       | pimlico.modules.nltk.nist_tokenize |
+------------+------------------------------------+
| Executable | yes                                |
+------------+------------------------------------+

Sentence splitting and tokenization using the
`NLTK NIST tokenizer <https://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.nist>`_.

Very simple tokenizer that's fairly language-independent and doesn't need
a trained model. Use this if you just need a rudimentary tokenization
(though more sophisticated than :mod:`~pimlico.modules.text.simple_tokenize`).


Inputs
======

+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                              |
+======+======================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`RawTextDocumentType <pimlico.datatypes.corpora.data_points.RawTextDocumentType>`> |
+------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name      | Type(s)                                                                                                                                                                |
+===========+========================================================================================================================================================================+
| documents | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+-----------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Options
=======

+--------------+-------------------------------------------------------------------------------------------+------+
| Name         | Description                                                                               | Type |
+==============+===========================================================================================+======+
| lowercase    | Lowercase all output. Default: False                                                      | bool |
+--------------+-------------------------------------------------------------------------------------------+------+
| non_european | Use the tokenizer's international_tokenize() method instead of tokenize(). Default: False | bool |
+--------------+-------------------------------------------------------------------------------------------+------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_nltk_nist_tokenizer_module]
   type=pimlico.modules.nltk.nist_tokenize
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_nltk_nist_tokenizer_module]
   type=pimlico.modules.nltk.nist_tokenize
   input_text=module_a.some_output
   lowercase=F
   non_european=F

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-nltk-nist_tokenize.conf`