from __future__ import print_function
# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import os

from pimlico.cli.shell.base import ShellCommand, ShellError

from pimlico.core.dependencies.python import PythonPackageOnPip
from pimlico.core.modules.options import str_to_bool
from pimlico.old_datatypes.base import PimlicoDatatype, PimlicoDatatypeWriter

__all__ = ["Word2VecModel", "Word2VecModelWriter"]


class NearestNeighboursCommand(ShellCommand):
    commands = ["neighbours", "nn"]
    help_text = "Print the nearest neighbours of the given word by cosine similarity in the vector space. You may " \
                "specify multiple words and include negative words by prefixing '-'"

    def execute(self, shell, *args, **kwargs):
        if len(args) == 0:
            raise ShellError("specify at least one word")
        model = shell.data.load_model()

        positive_words = [arg for arg in args if not arg.startswith("-")]
        negative_words = [arg[1:] for arg in args if arg.startswith("-")]
        for w in positive_words + negative_words:
            if w not in model.vocab:
                print("WARNING: %s not in vocabulary, leaving out" % w)
        # Filter out OOVs
        positive_words = [w for w in positive_words if w in model.vocab]
        negative_words = [w for w in negative_words if w in model.vocab]

        if len(positive_words + negative_words) == 0:
            raise ShellError("no non-OOV query terms")

        similar = model.most_similar(positive=positive_words, negative=negative_words)

        for word, score in similar:
            print("%s  (%.3f)" % (word, score))


class VectorCommand(ShellCommand):
    commands = ["vector", "vec"]
    help_text = "Output (some of) the values of a word vector. Use norm=T to apply Euclidean normalization"

    def execute(self, shell, *args, **kwargs):
        from gensim.matutils import unitvec

        model = shell.data.load_model()
        vec = model[args[0]]

        norm = str_to_bool(kwargs.pop("norm", False))
        if norm:
            vec = unitvec(vec)

        print(vec)


class SimilarityCommand(ShellCommand):
    commands = ["similarity", "sim"]
    help_text = "Output the similarity of two words by cosine in the vector space"

    def execute(self, shell, *args, **kwargs):
        model = shell.data.load_model()
        for word in args[:2]:
            if not word in model.vocab:
                raise ShellError("word '%s' is not in the vocabulary" % word)
        print(model.similarity(args[0], args[1]))


class Word2VecModel(PimlicoDatatype):
    """
    Datatype for storing Gensim-trained word2vec embeddings.

    .. seealso::

       Datatype :class:`pimlico.datatypes.embeddings.Embeddings`
           Another, more generic way, to write the same data, which should generally be used in preference
           to this one. ``Embeddings`` does not depend on Gensim, but can be converted to Gensim's data structure
           easily.

    """
    shell_commands = [NearestNeighboursCommand(), VectorCommand(), SimilarityCommand()]

    def __init__(self, base_dir, pipeline, **kwargs):
        super(Word2VecModel, self).__init__(base_dir, pipeline, **kwargs)
        self._model = None
        # Old models don't have this set, so default to False
        self.verb_only = self.metadata.get("verb_only", False)

    def data_ready(self):
        return super(Word2VecModel, self).data_ready() and os.path.exists(os.path.join(self.data_dir, "vectors.bin"))

    def load_model(self):
        if self._model is None:
            from gensim.models.keyedvectors import KeyedVectors
            self._model = KeyedVectors.load_word2vec_format(os.path.join(self.data_dir, "vectors.bin"), binary=True)
        return self._model

    @property
    def model(self):
        return self.load_model()

    def get_software_dependencies(self):
        # Depend on Gensim, which can be installed using Pip
        return super(Word2VecModel, self).get_software_dependencies() + [
            PythonPackageOnPip("gensim")
        ]


class Word2VecModelWriter(PimlicoDatatypeWriter):
    """
    .. note::

       Generally, it's preferable to use :class:`pimlico.datatypes.embeddings.Embeddings`, which is more
       generic, so easier to connect up with general vector/embedding-handling modules.

    """
    def __init__(self, base_dir, verb_only=False, **kwargs):
        super(Word2VecModelWriter, self).__init__(base_dir, **kwargs)
        # Provide writing by setting self.word2vec_model for backwards compatibility
        self.word2vec_model = None
        self.metadata["verb_only"] = verb_only
        self.require_tasks("vectors")

    def write_word2vec_model(self, model):
        self.write_keyed_vectors(model.wv)

    def write_keyed_vectors(self, vectors):
        vectors.save_word2vec_format(os.path.join(self.data_dir, "vectors.bin"), binary=True)
        self.task_complete("vectors")

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(Word2VecModelWriter, self).__exit__(exc_type, exc_val, exc_tb)
        # Provide writing by setting self.word2vec_model for backwards compatibility
        if "vectors" in self.incomplete_tasks and self.word2vec_model is not None:
            self.word2vec_model.wv.save_word2vec_format(os.path.join(self.data_dir, "vectors.bin"), binary=True)
