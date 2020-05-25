import os

from gensim.models import KeyedVectors

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        path = self.info.options["path"]
        binary = self.info.options["binary"]
        limit = self.info.options["limit"]

        # See whether a vocab file was provided: typically it has the same basename and a "vocab" extension
        vocab_path = "{}.vocab".format(path.rpartition(".")[0])
        if os.path.exists(vocab_path):
            self.log.info("Reading vocab from {}".format(vocab_path))
        else:
            self.log.info("No vocab file found")
            # No vocab file: don't pass one into the reader
            vocab_path = None

        # Use Gensim's tool to load the data
        self.log.info("Loading word2vec vectors from {}".format(path))
        if limit:
            self.log.info("Limiting to the first {:,} vectors".format(limit))
        vectors = KeyedVectors.load_word2vec_format(path, binary=binary, fvocab=vocab_path, limit=limit)

        # If there were spaces in any of the words, this is a problem for the w2v format, since the vocab
        # is stored in a space-separated file! When Pimlico writes out w2v vectors, it replaces spaces,
        # so we reverse that now
        vectors.vocab = dict(
            (replace_spaces(word), v) for (word, v) in vectors.vocab.items()
        )
        # Also apply inverse mapping to index2word
        vectors.index2word = [replace_spaces(word) for word in vectors.index2word]

        # Get the vectors from the model
        # We can use these to store embeddings in the Pimlico format
        with self.info.get_output_writer() as writer:
            writer.write_keyed_vectors(vectors)


def replace_spaces(word):
    return word.replace(u"<space>", u" ").replace(u"<nbspace>", u"\u00A0")
