from itertools import islice

import numpy

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.embeddings import EmbeddingsWriter
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        path = self.info.options["path"]
        limit = self.info.options["limit"]

        if path.endswith(".zip"):
            raise IOError("FastText reader cannot currently handle Facebook's bin+text vector format (.zip)")
        elif not path.endswith(".vec"):
            raise IOError("FastText reader can currently only handle Facebook's text vector format (.vec)")

        # The first line of the file gives the number of vectors and dimensionality
        with open(path, "r") as vec_file:
            lines = iter(vec_file)
            num_lines, __, embedding_size = next(lines).partition(" ")
            num_lines, embedding_size = int(num_lines), int(embedding_size)

            self.log.info("File contains {} vectors of dimensionality {}".format(num_lines, embedding_size))
            if limit and limit < num_lines:
                read_lines = limit
                self.log.info("Only reading {} vectors".format(read_lines))
            else:
                read_lines = num_lines

            # Prepare a numpy array to put all the vectors in
            vectors = numpy.zeros((read_lines, embedding_size), dtype=numpy.float32)

            words = []

            pbar = get_progress_bar(read_lines, title="Reading")
            for i, line in enumerate(pbar(islice(lines, read_lines))):
                line = line.decode("utf8")
                word, __, vector = line.partition(u" ")
                vector = [float(x) for x in vector.split()]

                words.append(word)
                vectors[i] = vector

        # We don't know word counts, so just set them to a descending count, so that they get ordered correctly
        word_counts = [(word, len(words)-1-i) for word, i in enumerate(words)]

        output_dir = self.info.get_absolute_output_dir("embeddings")
        self.log.info("Writing embeddings to {}".format(output_dir))
        with EmbeddingsWriter(output_dir) as writer:
            writer.write_word_counts(word_counts)
            writer.write_vectors(vectors)
