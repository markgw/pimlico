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
            self._len = sum(1 for doc_name, doc in self.indexed_corpus if not is_invalid_doc(doc))
        return self._len

    def __iter__(self):
        for doc_name, doc in self.indexed_corpus:
            if not is_invalid_doc(doc):
                # The document is currently a list of sentences, where each is a list of word IDs
                # Count up the occurrences of each ID in the document to get the bag of words for Gensim
                word_counter = Counter(
                    word_id for sentence in doc.lists for word_id in sentence if word_id not in self.ignore_ids
                )
                yield list(word_counter.iteritems())


def word_relevance_for_topic(topic_word_probs, word_probs, l=0.6):
    """
    Computes a relevance score for every word in the vocabulary for
    a given topic, following the definition of relevance from
    Sievert & Shirley (ILLVI, 2014).

    Distributions p(w | t) and p(w) should be given as numpy 1-D arrays,
    with length the number of words in the vocabulary.

    Lambda (l) specifies the balance between plain topic word probability
    and word-topic lift, with lambda=1 giving just the former and lambda=0
    just the latter. See the paper for more details.

    relevance(w, t, l) = l * log(p(w|t)) + (1 - l)*log(p(w|t) / p(w))

    """
    import numpy as np
    return l * np.log(topic_word_probs) + (1-l) * np.log(topic_word_probs / word_probs)
