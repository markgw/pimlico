from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.modules.input.embeddings.glove.read import load_glove_format


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        path = self.info.options["path"]

        # Use Gensim's tool to load the data
        self.log.info("Loading GloVe vectors from {}".format(path))
        vectors = load_glove_format(path, log=self.log)

        # Get the vectors from the model
        # We can use these to store embeddings in the Pimlico format
        with self.info.get_output_writer() as writer:
            writer.write_keyed_vectors(vectors)
