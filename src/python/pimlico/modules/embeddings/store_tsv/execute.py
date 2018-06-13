from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.embeddings import TSVVecFilesWriter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        embeddings = self.info.get_input("embeddings")

        # Output to the file
        with TSVVecFilesWriter(self.info.get_absolute_output_dir("embeddings")) as writer:
            writer.write_vectors(embeddings.vectors)
            writer.write_vocab_with_counts(embeddings.word_counts)
