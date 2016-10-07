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

This module is simply a wrapper to call `Gensim <https://radimrehurek.com/gensim/models/word2vec.html>`_'s Python
(+C) implementation of word2vec on a Pimlico corpus.


Inputs
======

+------+-------------------------------------+
| Name | Type(s)                             |
+======+=====================================+
| text | TarredCorpus<TokenizedDocumentType> |
+------+-------------------------------------+

Outputs
=======

+-------+----------------------------------------------------+
| Name  | Type(s)                                            |
+=======+====================================================+
| model | :class:`~pimlico.datatypes.word2vec.Word2VecModel` |
+-------+----------------------------------------------------+

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

