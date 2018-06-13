from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.modules.embeddings.store_word2vec.info import Word2VecFilesWriter


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        embeddings = self.info.get_input("embeddings")
        # Convert to Gensim KeyedVectors
        keyed_vectors = embeddings.to_keyed_vectors()

        # Output to the file
        with Word2VecFilesWriter(self.info.get_absolute_output_dir("embeddings")) as writer:
            # Use Gensim's output method to write in word2vec format
            vec_path = writer.get_absolute_path(writer.filenames[0])
            self.log.info("Writing vectors to {}".format(vec_path))
            keyed_vectors.save_word2vec_format(
                vec_path,
                fvocab=writer.get_absolute_path(writer.filenames[1]),
                binary=True,
            )
            # Both files have been written
            writer.file_written(writer.filenames[0])
            writer.file_written(writer.filenames[1])
