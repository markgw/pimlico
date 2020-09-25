Embeddings
~~~~~~~~~~


.. py:module:: pimlico.modules.embeddings


Modules for extracting features from which to learn word embeddings from corpora, and for training embeddings.

Some of these don't actually learn the embeddings, they just produce features which can then be fed into an embedding
learning module, such as a form of matrix factorization. Note that you can train embeddings not only using the
trainers here, but also using generic matrix manipulation techniques, for example the factorization methods
provided by sklearn.



.. toctree::
   :maxdepth: 2
   :titlesonly:

   pimlico.modules.embeddings.fasttext
   pimlico.modules.embeddings.normalize
   pimlico.modules.embeddings.store_embeddings
   pimlico.modules.embeddings.store_tsv
   pimlico.modules.embeddings.store_word2vec
   pimlico.modules.embeddings.word2vec
