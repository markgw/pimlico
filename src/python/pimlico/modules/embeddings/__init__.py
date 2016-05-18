"""
Embedding feature extractors and trainers

Modules for extracting features from which to learn word embeddings from corpora, and for training embeddings.

Some of these don't actually learn the embeddings, they just produce features which can then be fed into an embedding
learning module, such as a form of matrix factorization. Note that you can train embeddings not only using the
trainers here, but also using generic matrix manipulation techniques, for example the factorization methods
provided by sklearn.

"""