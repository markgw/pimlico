from pimlico.core.modules.base import BaseModuleExecutor


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        embeddings = self.info.get_input("embeddings")
        # Convert to Gensim KeyedVectors
        keyed_vectors = embeddings.to_keyed_vectors()

        spaces = sum(1 for w in keyed_vectors.index2word if u" " in w or u"\u00A0" in w)
        if spaces > 0:
            self.log.info("Some words ({}) include spaces: replacing with '<space>', so they don't mess up the "
                          "w2v vocab".format(spaces))
            # If there are spaces in any of the words, this is a problem for the w2v format, since the vocab
            # is stored in a space-separated file!
            keyed_vectors.vocab = dict(
                (replace_spaces(word), v) for (word, v) in keyed_vectors.vocab.items()
            )
            # Apply the same mapping to index2word
            keyed_vectors.index2word = [replace_spaces(word) for word in keyed_vectors.index2word]

        # Output to the file
        with self.info.get_output_writer("embeddings") as writer:
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


def replace_spaces(word):
    return word.replace(u" ", u"<space>").replace(u"\u00A0", u"<nbspace>")
