Corpus vocab builder
~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.corpora.vocab_builder

+------------+---------------------------------------+
| Path       | pimlico.modules.corpora.vocab_builder |
+------------+---------------------------------------+
| Executable | yes                                   |
+------------+---------------------------------------+

Builds a dictionary (or vocabulary) for a tokenized corpus. This is a data structure that assigns an integer
ID to every distinct word seen in the corpus, optionally applying thresholds so that some words are left out.

Similar to :mod:`pimlico.modules.features.vocab_builder`, which builds two vocabs, one for terms and one for
features.

May specify a list of stopwords, which will be ignored, even if they're found in the corpus.
The filter to remove frequent words (controlled  by `max_prop`) will potentially add further
stopwords, so the resulting list is output as `stopwords`.


Inputs
======

+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                                |
+======+========================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-----------+---------------------------------------------------------------+
| Name      | Type(s)                                                       |
+===========+===============================================================+
| vocab     | :class:`dictionary <pimlico.datatypes.dictionary.Dictionary>` |
+-----------+---------------------------------------------------------------+
| stopwords | :class:`string_list <pimlico.datatypes.core.StringList>`      |
+-----------+---------------------------------------------------------------+


Options
=======

+-----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| Name      | Description                                                                                                                                                                                                                                                                                                                                                  | Type                            |
+===========+==============================================================================================================================================================================================================================================================================================================================================================+=================================+
| include   | Ensure that certain words are always included in the vocabulary, even if they don't make it past the various filters, or are never seen in the corpus. Give as a comma-separated list                                                                                                                                                                        | comma-separated list of strings |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| limit     | Limit vocab size to this number of most common entries (after other filters)                                                                                                                                                                                                                                                                                 | int                             |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| max_prop  | Include terms that occur in max this proportion of documents                                                                                                                                                                                                                                                                                                 | float                           |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| oov       | Represent OOVs using the given string in the vocabulary. Used to represent chars that will be out of vocabulary after applying threshold/limit filters. Included in the vocabulary even if the count is 0                                                                                                                                                    | string                          |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| prune_at  | Prune the dictionary if it reaches this size. Setting a lower value avoids getting stuck with too big a dictionary to be able to prune and slowing things down, but means that the final pruning will less accurately reflect the true corpus stats. Should be considerably higher than limit (if used). Set to 0 to disable. Default: 2M (Gensim's default) | int                             |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+
| threshold | Minimum number of occurrences required of a term to be included                                                                                                                                                                                                                                                                                              | int                             |
+-----------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+---------------------------------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_vocab_builder_module]
   type=pimlico.modules.corpora.vocab_builder
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_vocab_builder_module]
   type=pimlico.modules.corpora.vocab_builder
   input_text=module_a.some_output
   include=word1,word2,... 
   limit=10k
   oov=text
   prune_at=2000000
   threshold=100

Example pipelines
=================

This module is used by the following :ref:`example pipelines <example-pipelines>`. They are examples of how the module can be used together with other modules in a larger pipeline.

 * :ref:`example-pipeline-train-tms-example`
 * :ref:`example-pipeline-custom-module-example`

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-corpora-vocab_builder.conf`

