Word2vec embedding trainer
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.word2vec

+------------+-------------------------------------+
| Path       | pimlico.modules.embeddings.word2vec |
+------------+-------------------------------------+
| Executable | yes                                 |
+------------+-------------------------------------+

Word2vec embedding learning algorithm, using `Gensim <https://radimrehurek.com/gensim/>`_'s implementation.

Find out more about `word2vec <https://code.google.com/archive/p/word2vec/>`_.

This module is simply a wrapper to call `Gensim Python (+C) <https://radimrehurek.com/gensim/models/word2vec.html>`_'s
implementation of word2vec on a Pimlico corpus.

Does not support Python 2 since Gensim has dropped Python 2 support.


*This module does not support Python 2, so can only be used when Pimlico is being run under Python 3*

Inputs
======

+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name | Type(s)                                                                                                                                                                |
+======+========================================================================================================================================================================+
| text | :class:`grouped_corpus <pimlico.datatypes.corpora.grouped.GroupedCorpus>` <:class:`TokenizedDocumentType <pimlico.datatypes.corpora.tokenized.TokenizedDocumentType>`> |
+------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Outputs
=======

+-------+---------------------------------------------------------------+
| Name  | Type(s)                                                       |
+=======+===============================================================+
| model | :class:`embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+-------+---------------------------------------------------------------+


Options
=======

+------------------+-----------------------------------------------------------------------------------------------------------------------------------+------+
| Name             | Description                                                                                                                       | Type |
+==================+===================================================================================================================================+======+
| iters            | number of iterations over the data to perform. Default: 5                                                                         | int  |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------+------+
| min_count        | word2vec's min_count option: prunes the dictionary of words that appear fewer than this number of times in the corpus. Default: 5 | int  |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------+------+
| negative_samples | number of negative samples to include per positive. Default: 5                                                                    | int  |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------+------+
| size             | number of dimensions in learned vectors. Default: 200                                                                             | int  |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------+------+

Example config
==============

This is an example of how this module can be used in a pipeline config file.

.. code-block:: ini
   
   [my_word2vec_module]
   type=pimlico.modules.embeddings.word2vec
   input_text=module_a.some_output
   

This example usage includes more options.

.. code-block:: ini
   
   [my_word2vec_module]
   type=pimlico.modules.embeddings.word2vec
   input_text=module_a.some_output
   iters=5
   min_count=5
   negative_samples=5
   size=200

Test pipelines
==============

This module is used by the following :ref:`test pipelines <test-pipelines>`. They are a further source of examples of the module's usage.

 * :ref:`test-config-embeddings-word2vec.conf`

