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

Input comes from tokenized data and a pre-built dictionary. Simply run your input corpus through
:mod:`pimlico.modules.corpora.vocab_builder` to build a dictionary.


Inputs
======

+------------+------------------------------------------------------------------------+
| Name       | Type(s)                                                                |
+============+========================================================================+
| text       | :class:`TokenizedCorpus <pimlico.datatypes.tokenized.TokenizedCorpus>` |
+------------+------------------------------------------------------------------------+
| dictionary | :class:`Dictionary <pimlico.datatypes.dictionary.Dictionary>`          |
+------------+------------------------------------------------------------------------+

Outputs
=======

+---------------+------------------------------------------------------------+
| Name          | Type(s)                                                    |
+===============+============================================================+
| term_features | :class:`~pimlico.datatypes.features.TermFeatureListCorpus` |
+---------------+------------------------------------------------------------+

