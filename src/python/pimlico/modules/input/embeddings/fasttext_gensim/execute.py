from gensim.models.wrappers.fasttext import FastText

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.old_datatypes.embeddings import EmbeddingsWriter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        path = self.info.options["path"]

        # Use Gensim's tool to load the data
        self.log.info("Loading FastText vectors from {}".format(path))
        fasttext = FastText.load_fasttext_format(path)

        # Get the vectors from the model
        # We can use these to store embeddings in the Pimlico format
        # This will throw away information specific to FastText (the things added in the FastTextKeyedVectors class)
        output_dir = self.info.get_absolute_output_dir("embeddings")
        self.log.info("Writing embeddings to {}".format(output_dir))
        with EmbeddingsWriter(output_dir) as writer:
            writer.write_keyed_vectors(fasttext.wv)
