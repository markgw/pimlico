"""
Datatypes to store embedding vectors, together with their words.

The main datatype here, :class:`Embeddings`, is the main datatype that should be used
for passing embeddings between modules.

We also provide a simple file collection datatype that stores the files used by
Tensorflow, for example, as input to the Tensorflow Projector.
Modules that need data in this format can use this datatype, which makes it
easy to convert from other formats.

"""
from __future__ import absolute_import

from builtins import str
from past.builtins import basestring
from builtins import object
from io import open

import os

from pimlico.core.dependencies.python import numpy_dependency
from pimlico.datatypes import PimlicoDatatype, NamedFileCollection
from pimlico.datatypes.files import NamedFileCollection
from pimlico.utils.core import cached_property

__all__ = ["Embeddings", "TSVVecFiles", "Word2VecFiles"]


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
    datatype_name = "embeddings"

    def get_software_dependencies(self):
        return super(Embeddings, self).get_software_dependencies() + [numpy_dependency]

    def get_writer_software_dependencies(self):
        return super(Embeddings, self).get_writer_software_dependencies() + [numpy_dependency]

    class Reader(object):
        class Setup(object):
            def get_required_paths(self):
                return ["vectors.npy", "vocab.csv"]

        @cached_property
        def vectors(self):
            import numpy
            with open(os.path.join(self.data_dir, "vectors.npy"), "rb") as f:
                return numpy.load(f, allow_pickle=False)

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
            with open(os.path.join(self.data_dir, "vocab.csv"), "rb") as f:
                reader = csv.reader(f)
                return [(row[0].decode("utf-8"), int(row[1].decode("utf-8"))) for row in reader]

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

        def word_vec(self, word, norm=False):
            """
            Accept a single word as input.
            Returns the word's representation in vector space, as a 1D numpy array.

            """
            return self.word_vecs([word], norm=norm)

        def word_vecs(self, words, norm=False):
            """
            Accept multiple words as input.
            Returns the words' representations in vector space, as a 1D numpy array.

            """
            try:
                word_ids = [self.vocab[w].index for w in words]
            except KeyError as e:
                raise KeyError("word not in vocabulary: {}".format(e))
            if norm:
                return self.normed_vectors[word_ids]
            else:
                return self.vectors[word_ids]

        def to_keyed_vectors(self):
            from gensim.models.keyedvectors import KeyedVectors, Vocab as GensimVocab
            kvecs = KeyedVectors(self.vector_size)
            index2vocab = [GensimVocab(word=v.word, count=v.count, index=v.index) for v in self.index2vocab]
            kvecs.vocab = dict((v.word, v) for v in index2vocab)
            kvecs.index2word = self.index2word
            kvecs.syn0 = self.vectors
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

    class Writer(object):
        required_tasks = ["vocab", "vectors"]

        def write_vectors(self, arr):
            """
            Write out vectors from a Numpy array
            """
            import numpy
            with open(os.path.join(self.data_dir, "vectors.npy"), "wb") as f:
                numpy.save(f, arr, allow_pickle=False)
            self.task_complete("vectors")

        def write_word_counts(self, word_counts):
            """
            Write out vocab from a list of words with counts.

            :param word_counts: list of (unicode, int) pairs giving each word and its count. Vocab indices are
                determined by the order of words
            """
            import csv
            with open(os.path.join(self.data_dir, "vocab.csv"), "wb") as f:
                writer = csv.writer(f)
                for word, count in word_counts:
                    writer.writerow([str(word).encode("utf-8"), str(count).encode("utf-8")])
            self.task_complete("vocab")

        def write_vocab_list(self, vocab_items):
            """
            Write out vocab from a list of vocab items (see ``Vocab``).

            :param vocab_items: list of ``Vocab`` s
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

    def __init__(self, *args, **kwargs):
        super(TSVVecFiles, self).__init__(["embeddings.tsv", "metadata.tsv"], *args, **kwargs)

    class Reader(object):
        def get_embeddings_data(self):
            return self.read_file(self.filenames[0])

        def get_embeddings_metadata(self):
            return self.read_file(self.filenames[1])

    class Writer(object):
        def write_vectors(self, array):
            import csv

            with open(self.get_absolute_path(self.filenames[0]), "wb") as f:
                writer = csv.writer(f, dialect="excel-tab")
                # Write each row
                for vec in array:
                    writer.writerow([str(val).encode("utf-8") for val in vec])
            self.file_written(self.filenames[0])

        def write_vocab_with_counts(self, word_counts):
            import csv

            with open(self.get_absolute_path(self.filenames[1]), "wb") as f:
                writer = csv.writer(f, dialect="excel-tab")
                writer.writerow(["Word", "Count"])
                for word, count in word_counts:
                    writer.writerow([str(word).encode("utf-8"), str(count).encode("utf-8")])
            self.file_written(self.filenames[1])

        def write_vocab_without_counts(self, words):
            import csv

            with open(self.get_absolute_path(self.filenames[1]), "wb") as f:
                writer = csv.writer(f, dialect="excel-tab")
                writer.writerow(["Word"])
                for word in words:
                    writer.writerow([str(word).encode("utf-8")])
            self.file_written(self.filenames[1])


class Word2VecFiles(NamedFileCollection):
    datatype_name = "word2vec_files"

    def __init__(self, *args, **kwargs):
        super(Word2VecFiles, self).__init__(["embeddings.bin", "embeddings.vocab"], *args, **kwargs)
