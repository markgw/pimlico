# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

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

from builtins import str, input
from past.builtins import basestring
from builtins import object

import io
import os

from backports import csv

from pimlico.core.dependencies.python import numpy_dependency, PythonPackageOnPip, fasttext_dependency
from pimlico.datatypes import PimlicoDatatype
from pimlico.datatypes.files import NamedFileCollection
from pimlico.utils.core import cached_property

__all__ = ["Vocab", "Embeddings", "TSVVecFiles", "Word2VecFiles",
           "DocEmbeddingsMapper", "FixedEmbeddingsDocMapper", "FastTextDocMapper"]


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

    Since we don't depend on Gensim, this datatype supports Python 2. However, if you
    try to use the mapping to Gensim's type, this will only work with Gensim installed
    and therefore also depends on Python 3.

    """
    datatype_name = "embeddings"
    datatype_supports_python2 = True

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
            with io.open(os.path.join(self.data_dir, "vectors.npy"), "rb") as f:
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
            with io.open(os.path.join(self.data_dir, "vocab.csv"), "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                return [(row[0], int(row[1])) for row in reader]

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
            with io.open(os.path.join(self.data_dir, "vocab.csv"), "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                for word, count in word_counts:
                    writer.writerow([str(word), str(count)])
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

    def run_browser(self, reader, opts):
        """
        Just output some info about the embeddings.

        We could also iterate through some of the words or provide other inspection tools,
        but for now we don't do that.

        """
        import numpy as np
        from sklearn.metrics import euclidean_distances
        from sklearn.metrics.pairwise import cosine_distances

        print("Reading embeddings...")
        num_vectors = len(reader)
        vector_size = reader.vector_size
        print("Embeddings for {:,} words, of {:,} dimensions".format(num_vectors, vector_size))
        # Select a few embeddings at random
        rand_ids = np.random.choice(num_vectors, 10)
        rand_vecs = reader.vectors[rand_ids]
        print("\nNearest neighbours for some random embeddings, using Euclidean distance")
        for rand_id, rand_vec in zip(rand_ids, rand_vecs):
            nns = np.argsort(euclidean_distances(rand_vec.reshape(1, -1), reader.vectors))[0]
            word, count = reader.word_counts[rand_id]
            print("  {} ({:,}): {}".format(
                word, count,
                ", ".join(reader.word_counts[i][0] for i in nns[:10])
            ))
        print("\nNearest neighbours for some random embeddings, using cosine distance")
        for rand_id, rand_vec in zip(rand_ids, rand_vecs):
            nns = np.argsort(cosine_distances(rand_vec.reshape(1, -1), reader.vectors))[0]
            word, count = reader.word_counts[rand_id]
            print("  {} ({:,}): {}".format(
                word, count,
                ", ".join(reader.word_counts[i][0] for i in nns[:10])
            ))


class TSVVecFiles(NamedFileCollection):
    """
    Embeddings stored in TSV files. This format is used by Tensorflow and can be used, for example,
    as input to the Tensorflow Projector.

    It's just a TSV file with each vector on a row, and another metadata TSV file with the
    names associated with the points and the counts. The counts are not necessary, so the metadata
    can be written without them if necessary.

    """
    datatype_name = "tsv_vec_files"
    datatype_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(TSVVecFiles, self).__init__(["embeddings.tsv", "metadata.tsv"], *args, **kwargs)

    class Reader(object):
        def get_embeddings_data(self):
            return self.read_file(self.filenames[0])

        def get_embeddings_metadata(self):
            return self.read_file(self.filenames[1])

    class Writer(object):
        def write_vectors(self, array):
            with io.open(self.get_absolute_path(self.filenames[0]), "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, dialect="excel-tab")
                # Write each row
                for vec in array:
                    writer.writerow([str(val) for val in vec])
            self.file_written(self.filenames[0])

        def write_vocab_with_counts(self, word_counts):
            with io.open(self.get_absolute_path(self.filenames[1]), "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, dialect="excel-tab")
                writer.writerow([u"Word", u"Count"])
                for word, count in word_counts:
                    writer.writerow([str(word), str(count)])
            self.file_written(self.filenames[1])

        def write_vocab_without_counts(self, words):
            with io.open(self.get_absolute_path(self.filenames[1]), "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, dialect="excel-tab")
                writer.writerow([u"Word"])
                for word in words:
                    writer.writerow([str(word)])
            self.file_written(self.filenames[1])


class Word2VecFiles(NamedFileCollection):
    datatype_name = "word2vec_files"
    datatype_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(Word2VecFiles, self).__init__(["embeddings.bin", "embeddings.vocab"], *args, **kwargs)


class FastTextEmbeddings(PimlicoDatatype):
    """
    Simple wrapper for fastText embeddings, stored and written using the
    `fastText Python package <https://fasttext.cc/docs/en/python-module.html>`.

    Depends on the fastText package, installed via Pip.

    """
    datatype_name = "fasttext_embeddings"
    datatype_supports_python2 = True

    def get_software_dependencies(self):
        return super(FastTextEmbeddings, self).get_software_dependencies() + [fasttext_dependency]

    class Reader:
        def load_model(self):
            import fasttext

            model_path = os.path.join(self.data_dir, "model.bin")
            return fasttext.load_model(model_path)

    class Writer:
        required_tasks = ["model"]

        def save_model(self, model):
            model_path = os.path.join(self.data_dir, "model.bin")
            model.save_model(model_path)
            self.task_complete("model")


class DocEmbeddingsMapper(PimlicoDatatype):
    """
    Abstract datatype.

    An embedding loader provides a method to take a list of tokens (e.g. a tokenized document)
    and produce an embedding for each token.
    It will not necessarily be able to produce an embedding for *any* given term, so
    might return None for some tokens.

    This is more general than the :class:`~.Embeddings` datatype, as it allows this
    method to potentially produce embeddings for an infinite set of terms. Conversely,
    it is not able to say which set of terms it can produce embeddings for.

    It provides a unified interface to composed embeddings, like fastText, which can
    use sub-word information to produce embeddings of OOVs; context-sensitive
    embeddings, like BERT, which taken into account the context of a token; and fixed
    embeddings, which just return a fixed embedding for in-vocab terms.

    Some subtypes are just wrappers for fixed sets of embeddings.

    """
    datatype_name = "doc_embeddings_mapper"

    def get_software_dependencies(self):
        return super(DocEmbeddingsMapper, self).get_software_dependencies() + [numpy_dependency]

    def run_browser(self, reader, opts):
        """
        Simple tool to display embeddings for the words of user-entered sentences.
        """
        print("Enter a sentence to see its word vectors. Ctrl+D to exit")
        try:
            while True:
                input_text = input("> ")
                sentence = input_text.split()
                embeddings = reader.get_embeddings(sentence)
                for w, (word, embedding) in enumerate(zip(sentence, embeddings)):
                    print("{} {}: {}".format(w, word, embedding))
        except EOFError:
            print("Exiting")

    class Reader:
        def get_embeddings(self, tokens):
            """
            Subclasses should produce a list, with an item for each token. The
            item may be None, or a numpy array containing a vector for the token.

            :param tokens: list of strings
            :return: list of embeddings
            """
            raise NotImplementedError("abstract datatype does not implement get_embeddings")


class FastTextDocMapper(DocEmbeddingsMapper):
    datatype_name = "fasttext_doc_embeddings_mapper"

    def get_software_dependencies(self):
        return super(FastTextDocMapper, self).get_software_dependencies() + [fasttext_dependency]

    class Reader:
        @cached_property
        def model(self):
            import fasttext

            model_path = os.path.join(self.data_dir, "model.bin")
            return fasttext.load_model(model_path)

        def get_embeddings(self, tokens):
            return [self.model.get_word_vector(token) for token in tokens]

    class Writer:
        required_tasks = ["model"]

        def save_model(self, model):
            model_path = os.path.join(self.data_dir, "model.bin")
            model.save_model(model_path)
            self.task_complete("model")


class FixedEmbeddingsDocMapper(DocEmbeddingsMapper):
    datatype_name = "fixed_embeddings_doc_embeddings_mapper"

    class Reader(object):
        class Setup(object):
            def get_required_paths(self):
                return ["vectors.npy", "vocab.csv"]

        @cached_property
        def vectors(self):
            import numpy
            with io.open(os.path.join(self.data_dir, "vectors.npy"), "rb") as f:
                return numpy.load(f, allow_pickle=False)

        @cached_property
        def vector_size(self):
            return self.vectors.shape[1]

        @cached_property
        def word_counts(self):
            with io.open(os.path.join(self.data_dir, "vocab.csv"), "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                return [(row[0], int(row[1])) for row in reader]

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
            try:
                word_id = self.vocab[word].index
            except KeyError as e:
                raise KeyError("word not in vocabulary: {}".format(e))
            return self.vectors[word_id]

        def __contains__(self, word):
            return word in self.vocab

        def get_embeddings(self, tokens):
            return [self.word_vec(token) if token in self else None for token in tokens]

    class Writer(object):
        required_tasks = ["vocab", "vectors"]

        def write_vectors(self, arr):
            """Write out vectors from a Numpy array """
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
            with io.open(os.path.join(self.data_dir, "vocab.csv"), "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                for word, count in word_counts:
                    writer.writerow([str(word), str(count)])
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
