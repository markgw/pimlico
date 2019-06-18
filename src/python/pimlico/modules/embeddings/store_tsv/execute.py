from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        embeddings = self.info.get_input("embeddings")

        # Output to the file
        with self.info.get_output_writer("embeddings") as writer:
            writer.write_vectors(embeddings.vectors)
            writer.write_vocab_with_counts(embeddings.word_counts)
