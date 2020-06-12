from builtins import range
import warnings

from gensim import utils
from gensim.models.keyedvectors import Vocab, WordEmbeddingsKeyedVectors
from gensim.scripts.glove2word2vec import get_glove_info
from numpy import zeros, float32, ascontiguousarray

from pimlico.utils.progress import get_progress_bar

from smart_open import open


def load_glove_format(fname, fvocab=None, encoding='utf8', unicode_errors='strict', limit=None, log=None):
    """
    Modified version of Gensim's `load_word2vec_format()` to read GloVe vectors,
    which are stored in a very similar format.

    You can also do this using Gensim's `glove2word2vec()` and then reading with the
    standard word2vec reader, but this requires completely copying the file, which is
    unnecessary.

    Load the input-hidden weight matrix from the original C word2vec-tool format.

    If you trained the C model using non-utf8 encoding for words, specify that
    encoding in `encoding`.

    `unicode_errors`, default 'strict', is a string suitable to be passed as the `errors`
    argument to the unicode() (Python 2.x) or str() (Python 3.x) function. If your source
    file may include word tokens truncated in the middle of a multibyte unicode character
    (as is common from the original word2vec.c tool), 'ignore' or 'replace' may help.

    `limit` sets a maximum number of word-vectors to read from the file. The default,
    None, means read all.

    """
    if log is None:
        def _info(text):
            return
    else:
        _info = log.info

    counts = None
    if fvocab is not None:
        _info("Reading vocab file")
        counts = {}
        with open(fvocab) as fin:
            for line in fin:
                word, count = utils.to_unicode(line).strip().split()
                counts[word] = int(count)

    # First read the size of vectors and number of vectors, which in the word2vec
    # format are stored on the first line
    vocab_size, vector_size = get_glove_info(fname)
    _info("Reading {} vectors with {} dimensions".format(vocab_size, vector_size))

    with open(fname) as fin:
        if limit:
            vocab_size = min(vocab_size, limit)
        result = WordEmbeddingsKeyedVectors(vector_size)
        result.syn0 = zeros((vocab_size, vector_size), dtype=float32)

        def add_word(word, weights, from_line):
            word_id = len(result.vocab)
            if word in result.vocab:
                warnings.warn("duplicate word '{}' in {}:{:d}, ignoring all but first".format(word, fname, from_line))
                return
            if counts is None:
                # most common scenario: no vocab file given. just make up some bogus counts, in descending order
                result.vocab[word] = Vocab(index=word_id, count=vocab_size - word_id)
            elif word in counts:
                # use count from the vocab file
                result.vocab[word] = Vocab(index=word_id, count=counts[word])
            else:
                # vocab file given, but word is missing -- set count to None (TODO: or raise?)
                warnings.warn("vocabulary file is incomplete: '{}' is missing (line {:d}".format(word, from_line))
                result.vocab[word] = Vocab(index=word_id, count=None)
            result.syn0[word_id] = weights
            result.index2word.append(word)

        # If not logging, don't show a progress bar either
        if log is None:
            pbar = lambda x: x
        else:
            pbar = get_progress_bar(vocab_size, title="Reading")

        for line_no in pbar(range(vocab_size)):
            line = fin.readline()
            if line == b'':
                raise EOFError("unexpected end of input; is count incorrect or file otherwise damaged?")
            parts = utils.to_unicode(line.rstrip(), encoding=encoding, errors=unicode_errors).split(" ")
            if len(parts) != vector_size + 1:
                raise ValueError("invalid vector on line %s (is this really the text format?)" % line_no)
            word, weights = parts[0], [float32(x) for x in parts[1:]]
            add_word(word, weights, line_no)
    if result.syn0.shape[0] != len(result.vocab):
        result.syn0 = ascontiguousarray(result.syn0[: len(result.vocab)])
    assert (len(result.vocab), vector_size) == result.syn0.shape

    return result
