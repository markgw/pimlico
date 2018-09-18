"""
Utilities for using Gensim in Pimlico used across different modules.

"""
from collections import Counter

from pimlico.datatypes.corpora import is_invalid_doc


class GensimCorpus(object):
    """
    Type used to present an indexed corpus to Gensim for model training.
    Takes a GroupedCorpus with data point type :class:`~pimlico.datatypes.ints.IntegerListsDocumentType`
    and provides an iterator over the documents to yield each document's bag of words,
    using the word IDs already indexed.

    This is a simple utility, since the representations are already very similar.

    """
    def __init__(self, indexed_corpus, ignore_ids=None):
        self.indexed_corpus = indexed_corpus
        self.ignore_ids = ignore_ids or []

        self._len = None

    def __len__(self):
        if self._len is None:
            # We only yield valid docs, so count up how many there are
            self._len = sum(1 for doc in self.indexed_corpus if not isinstance(doc, InvalidDocument))
        return self._len

    def __iter__(self):
        for doc_name, doc in self.indexed_corpus:
            if not is_invalid_doc(doc):
                # The document is currently a list of sentences, where each is a list of word IDs
                # Count up the occurrences of each ID in the document to get the bag of words for Gensim
                word_counter = Counter(
                    word_id for sentence in doc for word_id in sentence if word_id not in self.ignore_ids
                )
                yield list(word_counter.iteritems())
