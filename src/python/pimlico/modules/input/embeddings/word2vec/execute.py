from gensim.models import KeyedVectors

from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        path = self.info.options["path"]
        binary = self.info.options["binary"]

        # Use Gensim's tool to load the data
        self.log.info("Loading word2vec vectors from {}".format(path))
        vectors = KeyedVectors.load_word2vec_format(path, binary=binary)

        # Get the vectors from the model
        # We can use these to store embeddings in the Pimlico format
        with self.info.get_output_writer() as writer:
            writer.write_keyed_vectors(vectors)
