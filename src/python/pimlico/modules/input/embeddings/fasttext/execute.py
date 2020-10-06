import fasttext
import numpy as np
from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        path = self.info.options["path"]

        model = fasttext.load_model(path)
        self.log.info("Loaded fastText model with {:,} embeddings of dimensionality {}".format(
            len(model.words), model.get_dimension()))

        self.log.info("Outputting to module directory")
        with self.info.get_output_writer("model") as writer:
            writer.save_model(model)

        self.log.info("Outputting fixed vectors")
        # We don't have word counts for the words in the vocab
        word_counts = [(word, 1) for word in model.words]
        vectors = np.zeros((len(word_counts), model.get_dimension()), dtype=np.float32)
        for w, (word, count) in enumerate(word_counts):
            vectors[w] = model[word]

        with self.info.get_output_writer("embeddings") as writer:
            writer.write_vectors(vectors)
            writer.write_word_counts(word_counts)
