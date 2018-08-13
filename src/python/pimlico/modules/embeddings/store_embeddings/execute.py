from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_embeddings = self.info.get_input("embeddings")

        with self.info.get_output_writer("embeddings") as writer:
            self.log.info("Writing vectors")
            writer.write_vectors(input_embeddings.vectors)
            self.log.info("Writing word counts")
            writer.write_word_counts(input_embeddings.word_counts)
