import os

from pimlico.old_datatypes.base import PimlicoDatatype, PimlicoDatatypeWriter
from pimlico.old_datatypes.files import NamedFileCollection, NamedFileCollectionWriter
from pimlico.utils.core import cached_property


class Vocab(object):
    """
    A single vocabulary item, used internally for collecting per-word frequency info. A simplified
    version of Gensim's ``Vocab``.

    """

    def __init__(self, word, index, count=0):
        self.word = word
        self.index = index
        self.count = count

    def __unicode__(self):
        return self.word

    def __str__(self):
        return self.word.encode("ascii", "replace")


class Embeddings(PimlicoDatatype):
    """
    Datatype to store embedding vectors, together with their words. Based on Gensim's ``KeyedVectors`` object,
    but adapted for use in Pimlico and so as not to depend on Gensim. (This means that this can be used
    more generally for storing embeddings, even when we're not depending on Gensim.)

    Provides a method to map to Gensim's ``KeyedVectors`` type for compatibility.

    Doesn't provide all of the functionality of ``KeyedVectors``, since the main purpose of this is for storage
    of vectors and other functionality, like similarity computations, can be provided by utilities or by
    direct use of Gensim.

    """
    def __init__(self, base_dir, pipeline, **kwargs):
        super(Embeddings, self).__init__(base_dir, pipeline, **kwargs)

    @cached_property
    def vectors(self):
        import numpy
        with open(os.path.join(self.data_dir, "vectors.npy"), "r") as f:
            return numpy.load(f)

    @cached_property
    def normed_vectors(self):
        import numpy
        vectors = self.vectors
        vectors /= numpy.sqrt((vectors ** 2.).sum(axis=1))[:, numpy.newaxis]
        return vectors

    @cached_property
    def vector_size(self):
        return self.vectors.shape[1]

    @cached_property
    def word_counts(self):
        import csv
        with open(os.path.join(self.data_dir, "vocab.csv"), "r") as f:
            reader = csv.reader(f)
            return [(row[0].decode("utf8"), int(row[1])) for row in reader]

    @cached_property
    def index2vocab(self):
        return [Vocab(word, i, count=count) for i, (word, count) in enumerate(self.word_counts)]

    @cached_property
    def index2word(self):
        return [v.word for v in self.index2vocab]

    @cached_property
    def vocab(self):
        # Build the vocab by indexing the vocab items (in index2word) by word
        return dict((v.word, v) for v in self.index2vocab)

    def __len__(self):
        return len(self.index2vocab)

    def word_vec(self, word):
        """
        Accept a single word as input.
        Returns the word's representation in vector space, as a 1D numpy array.

        """
        return self.word_vecs([word])

    def word_vecs(self, words):
        """
        Accept multiple words as input.
        Returns the words' representations in vector space, as a 1D numpy array.

        """
        try:
            word_ids = [self.vocab[w].index for w in words]
        except KeyError, e:
            raise KeyError("word not in vocabulary: {}".format(e))
        return self.vectors[word_ids]

    def to_keyed_vectors(self):
        from gensim.models.keyedvectors import KeyedVectors, Vocab as GensimVocab
        kvecs = KeyedVectors()
        index2vocab = [GensimVocab(word=v.word, count=v.count, index=v.index) for v in self.index2vocab]
        kvecs.vocab = dict((v.word, v) for v in index2vocab)
        kvecs.index2word = self.index2word
        kvecs.syn0 = self.vectors
        kvecs.vector_size = self.vector_size
        kvecs.init_sims()
        return kvecs

    def __getitem__(self, words):
        """
        Accept a single word or a list of words as input.

        If a single word: returns the word's representations in vector space, as
        a 1D numpy array.

        Multiple words: return the words' representations in vector space, as a
        2d numpy array: #words x #vector_size. Matrix rows are in the same order
        as in input.

        Example::

          >>> trained_model['office']
          array([ -1.40128313e-02, ...])

          >>> trained_model[['office', 'products']]
          array([ -1.40128313e-02, ...]
                [ -1.70425311e-03, ...]
                 ...)

        """
        if isinstance(words, basestring):
            # allow calls like trained_model['office'], as a shorthand for trained_model[['office']]
            words = [words]
        return self.word_vecs(words)

    def __contains__(self, word):
        return word in self.vocab


class EmbeddingsWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir, **kwargs):
        super(EmbeddingsWriter, self).__init__(base_dir, **kwargs)
        self.require_tasks("vocab", "vectors")

    def write_vectors(self, arr):
        """
        Write out vectors from a Numpy array
        """
        import numpy
        with open(os.path.join(self.data_dir, "vectors.npy"), "w") as f:
            numpy.save(f, arr)
        self.task_complete("vectors")

    def write_word_counts(self, word_counts):
        """
        Write out vocab from a list of words with counts.

        :param word_counts: list of (unicode, int) pairs giving each word and its count. Vocab indices are
            determined by the order of words
        """
        import csv
        with open(os.path.join(self.data_dir, "vocab.csv"), "w") as f:
            writer = csv.writer(f)
            for word, count in word_counts:
                writer.writerow([unicode(word).encode("utf8"), str(count)])
        self.task_complete("vocab")

    def write_vocab_list(self, vocab_items):
        """
        Write out vocab from a list of vocab items (see ``Vocab``).

        :param vocab_items: list of ``Vocab``s
        """
        self.write_word_counts([(v.word, v.count) for v in vocab_items])

    def write_keyed_vectors(self, *kvecs):
        """
        Write both vectors and vocabulary straight from Gensim's ``KeyedVectors`` data structure.
        Can accept multiple objects, which will then be concatenated in the output.

        """
        import numpy
        if len(kvecs) > 1:
            vecs = numpy.vstack(tuple(kv.syn0 for kv in kvecs))
        else:
            vecs = kvecs[0].syn0
        self.write_vectors(vecs)
        self.write_word_counts([(w, kv.vocab[w].count) for kv in kvecs for w in kv.index2word])


class TSVVecFiles(NamedFileCollection):
    """
    Embeddings stored in TSV files. This format is used by Tensorflow and can be used, for example,
    as input to the Tensorflow Projector.

    It's just a TSV file with each vector on a row, and another metadata TSV file with the
    names associated with the points and the counts. The counts are not necessary, so the metadata
    can be written without them if necessary.

    """
    datatype_name = "tsv_vec_files"
    filenames = ["embeddings.tsv", "metadata.tsv"]


class TSVVecFilesWriter(NamedFileCollectionWriter):
    """
    Write embeddings and their labels to TSV files, as used by Tensorflow.
    
    """
    filenames = ["embeddings.tsv", "metadata.tsv"]

    def write_vectors(self, array):
        import csv

        with open(self.get_absolute_path(self.filenames[0]), "w") as f:
            writer = csv.writer(f, dialect="excel-tab")
            # Write each row
            for vec in array:
                writer.writerow([str(val) for val in vec])
        self.file_written(self.filenames[0])

    def write_vocab_with_counts(self, word_counts):
        import csv

        with open(self.get_absolute_path(self.filenames[1]), "w") as f:
            writer = csv.writer(f, dialect="excel-tab")
            writer.writerow(["Word", "Count"])
            for word, count in word_counts:
                writer.writerow([unicode(word).encode("utf-8"), str(count)])
        self.file_written(self.filenames[1])

    def write_vocab_without_counts(self, words):
        import csv

        with open(self.get_absolute_path(self.filenames[1]), "w") as f:
            writer = csv.writer(f, dialect="excel-tab")
            writer.writerow(["Word"])
            for word in words:
                writer.writerow([unicode(word).encode("utf-8")])
        self.file_written(self.filenames[1])