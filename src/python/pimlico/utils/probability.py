from itertools import islice
import random
import itertools
from pimlico.utils.core import infinite_cycle


def limited_shuffle(iterable, buffer_size):
    """
    Some algorithms require the order of data to be randomized. An obvious solution is to put it all in
    a list and shuffle, but if you don't want to load it all into memory that's not an option. This method
    iterates over the data, keeping a buffer and choosing at random from the buffer what to put next.
    It's less shuffled than the simpler solution, but limits the amount of memory used at any one time
    to the buffer size.

    """
    buffer = []
    try:
        while len(buffer) < buffer_size:
            buffer.append(iterable.next())

        for next_val in iterable:
            # Pick a random item from the buffer to remove
            index = random.randint(0, len(buffer)-1)
            yield buffer.pop(index)
            # Add the new value to the buffer to replace the old one
            buffer.append(next_val)
    except StopIteration:
        # No more to take in, just return the rest in a random order
        random.shuffle(buffer)
        for v in buffer:
            yield v


def sequential_document_sample(corpus, start=None, shuffle=None, sample_rate=None):
    """
    Wrapper around a :class:`pimlico.datatypes.tar.TarredCorpus` to draw infinite samples of documents
    from the corpus, by iterating over the corpus (looping infinitely), yielding documents at random.
    If `sample_rate` is given, it should be a float between 0 and 1, specifying the rough proportion of
    documents to sample. A lower value spreads out the documents more on average.

    Optionally, the samples are shuffled within a limited scope. Set `shuffle` to the size of this scope (higher
    will shuffle more, but need to buffer more samples in memory).
    Otherwise (`shuffle=0`), they will appear in the order they were in the original corpus.

    If `start` is given, that number of documents will be skipped before drawing any samples. Set `start=0` to
    start at the beginning of the corpus. By default (`start=None`) a random point in the corpus will be skipped
    to before beginning.
    
    """
    if start is None:
        # Choose a random point in the dataset to start at
        start = random.randint(0, len(corpus)-1)
    # Start by reading the corpus from the start point onwards, then cycle forever
    doc_iter = itertools.chain(
        # Jump into the corpus the first time round
        corpus.archive_iter(skip=start, subsample=sample_rate),
        # Then loop over the corpus infinitely
        infinite_cycle(corpus.archive_iter(subsample=sample_rate))
    )
    if shuffle is not None:
        # Shuffle the data points (a bit) as we go
        doc_iter = iter(limited_shuffle(doc_iter, shuffle))
    return doc_iter


def sequential_sample(iterable, start=0, shuffle=None, sample_rate=None):
    """
    Draw infinite samples from an iterable, by iterating over it (looping infinitely), yielding items at random.
    If `sample_rate` is given, it should be a float between 0 and 1, specifying the rough proportion of
    documents to sample. A lower value spreads out the documents more on average.

    Optionally, the samples are shuffled within a limited scope. Set `shuffle` to the size of this scope (higher
    will shuffle more, but need to buffer more samples in memory).
    Otherwise (`shuffle=0`), they will appear in the order they were in the original corpus.

    If `start` is given, that number of documents will be skipped before drawing any samples. Set `start=0` to
    start at the beginning of the corpus. Note that setting this to a high number can result in a slow start-up, 
    if iterating over the items is slow.
    
    .. note::
       
       If you're sampling documents from a `TarredCorpus`, it's better to use :func:`sequential_document_sample`,
       since it makes use of `TarredCorpus`'s built-in features to do the skipping and sampling more efficiently.

    """
    # Cycle forever
    doc_iter = infinite_cycle(iterable)
    if sample_rate is not None and sample_rate != 1.:
        # Subsample to space out the items that get included
        doc_iter = subsample(doc_iter, sample_rate)
    if start > 0:
        # Skip some items at the start
        doc_iter = islice(doc_iter, start, None)
    if shuffle is not None:
        # Shuffle the data points (a bit) as we go
        doc_iter = iter(limited_shuffle(doc_iter, shuffle))
    return doc_iter


def subsample(iterable, sample_rate):
    """
    Subsample the given iterable at a given rate, between 0 and 1.
    
    """
    for item in iterable:
        if random.random() <= sample_rate:
            yield item
