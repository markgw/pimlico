Store in word2vec format
~~~~~~~~~~~~~~~~~~~~~~~~

.. py:module:: pimlico.modules.embeddings.store_word2vec

+------------+-------------------------------------------+
| Path       | pimlico.modules.embeddings.store_word2vec |
+------------+-------------------------------------------+
| Executable | yes                                       |
+------------+-------------------------------------------+

Takes embeddings stored in the default format used within Pimlico pipelines
(see :class:`~pimlico.datatypes.embeddings.Embeddings`) and stores them
using the ``word2vec`` storage format.

Uses the Gensim implementation of the storage, so depends on Gensim.


Inputs
======

+------------+---------------------------------------------------------------+
| Name       | Type(s)                                                       |
+============+===============================================================+
| embeddings | :class:`Embeddings <pimlico.datatypes.embeddings.Embeddings>` |
+------------+---------------------------------------------------------------+

Outputs
=======

+------------+------------------------------------------------------------------------+
| Name       | Type(s)                                                                |
+============+========================================================================+
| embeddings | :class:`~pimlico.modules.embeddings.store_word2vec.info.Word2VecFiles` |
+------------+------------------------------------------------------------------------+

