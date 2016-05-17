Embedding feature extractors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. py:module:: pimlico.modules.embeddings


Modules for extracting features from which to learn word embeddings from corpora.
These don't actually learn the embeddings, they just produce features which can then be fed into an embedding
learning module, such as a form of matrix factorization.



.. toctree::
   :maxdepth: 2
   :titlesonly:

   pimlico.modules.embeddings.dependencies
   pimlico.modules.embeddings.word2vec
