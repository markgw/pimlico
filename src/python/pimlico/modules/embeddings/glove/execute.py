# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html
import io
import os
import shutil
import subprocess
from itertools import islice
from operator import itemgetter

from pimlico.core.modules.execute import ModuleExecutionError

import numpy as np
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.utils.progress import get_progress_bar

from pimlico.utils.core import raise_from

from .deps import glove_dependency


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_corpus = self.info.get_input("text")
        opts = self.info.options
        glove_bins = glove_dependency.build_path
        vector_size = opts["vector_size"]

        tmp_dir = os.path.join(self.info.get_module_output_dir(absolute=True), "model_train_tmp")
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir)
        self.log.info("Storing temporary data between preparation stages in {}".format(tmp_dir))

        pbar = get_progress_bar(len(input_corpus), title="Preparing data")
        # Glove requires input as a single text file, with one document per line
        input_text_file = os.path.join(tmp_dir, "input.txt")
        with io.open(input_text_file, "w") as input_f:
            for doc_name, doc in pbar(input_corpus):
                # Just put all the words of the document on a single line
                input_f.write("{}\n".format(" ".join(word for sentence in doc.sentences for word in sentence)))

        # Keep the actual files produced by glove
        with self.info.get_output_writer("glove_output") as glove_output:
            # Run stage 1: prepare the vocab
            vocab_file = glove_output.get_absolute_path("vocab.txt")
            self.log.info("Running vocab_count to produce vocabulary in {}".format(vocab_file))
            vocab_cmd = [os.path.join(glove_bins, "vocab_count")]
            if opts["max_vocab"] > 0:
                vocab_cmd.extend(["-max-count", str(opts["max_vocab"])])
            if opts["min_count"] > 1:
                vocab_cmd.extend(["-min-count", str(opts["min_count"])])
            self.log.info("  Command: {}".format(" ".join(vocab_cmd)))
            try:
                with io.open(input_text_file, "rb") as input_f, io.open(vocab_file, "wb") as output_f:
                    subprocess.check_call(vocab_cmd, stdin=input_f, stdout=output_f)
            except subprocess.CalledProcessError as e:
                raise_from(ModuleExecutionError("call to GloVe's vocab_count failed: {}".format(e)), e)
            glove_output.file_written("vocab.txt")

            # Run stage 2: prepare co-occurrence counts
            cooccur_file = glove_output.get_absolute_path("cooccurrence.bin")
            self.log.info("Running cooccur to produce cooccurrences in {}".format(cooccur_file))
            cooccur_cmd = [
                os.path.join(glove_bins, "cooccur"),
                "-vocab-file", vocab_file,
                "-memory", "{:.1f}".format(opts["memory"]),
                "-symmetric", "1" if opts["symmetric"] else "0",
                "-window-size", str(opts["window_size"]),
                "-distance-weighting", "1" if opts["distance_weighting"] else "0",
            ]
            if opts["max_product"] is not None:
                cooccur_cmd.extend(["-max-product", str(opts["max_product"])])
            if opts["overflow_length"] is not None:
                cooccur_cmd.extend(["-overflow-length", str(opts["overflow_length"])])
            self.log.info("  Command: {}".format(" ".join(cooccur_cmd)))
            try:
                with io.open(input_text_file, "rb") as input_f, io.open(cooccur_file, "wb") as output_f:
                    subprocess.check_call(cooccur_cmd, stdin=input_f, stdout=output_f)
            except subprocess.CalledProcessError as e:
                raise_from(ModuleExecutionError("call to GloVe's cooccur failed: {}".format(e)), e)
            glove_output.file_written("cooccurrence.bin")

            # Run stage 3: shuffle
            cooccur_shuf_file = glove_output.get_absolute_path("cooccurrence.shuf.bin")
            self.log.info("Running shuffle to produce shuffled cooccurrences in {}".format(cooccur_shuf_file))
            shuf_cmd = [
                os.path.join(glove_bins, "shuffle"),
                "-memory", "{:.1f}".format(opts["memory"]),
            ]
            if opts["seed"] is not None:
                shuf_cmd.extend(["-seed", str(opts["seed"])])
            if opts["array_size"] is not None:
                shuf_cmd.extend(["-array-size", str(opts["array_size"])])
            self.log.info("  Command: {}".format(" ".join(shuf_cmd)))
            try:
                with io.open(cooccur_file, "rb") as input_f, io.open(cooccur_shuf_file, "wb") as output_f:
                    subprocess.check_call(shuf_cmd, stdin=input_f, stdout=output_f)
            except subprocess.CalledProcessError as e:
                raise_from(ModuleExecutionError("call to GloVe's shuffle failed: {}".format(e)), e)
            glove_output.file_written("cooccurrence.shuf.bin")

            # Run stage 4: train
            embeddings_file = glove_output.get_absolute_path("vectors.txt")
            embeddings_file_base = embeddings_file[:-4]
            self.log.info("Running glove to produce word embeddings in {}".format(embeddings_file))
            glove_cmd = [
                os.path.join(glove_bins, "glove"),
                "-vector-size", str(vector_size),
                "-threads", str(opts["threads"]),
                "-iter", str(opts["iter"]),
                "-eta", str(opts["eta"]),
                "-alpha", str(opts["alpha"]),
                "-x-max", str(opts["x_max"]),
                # Save in text format so we can easily read it in
                "-binary", "0",
                # Store vectors and context vectors
                "-model", "1",
                "-input-file", cooccur_shuf_file,
                "-vocab-file", vocab_file,
                "-save-file", embeddings_file_base,
            ]
            if opts["grad_clip"] is not None:
                glove_cmd.extend(["-grad-clip", str(opts["grad_clip"])])
            if opts["seed"] is not None:
                glove_cmd.extend(["-seed", str(opts["seed"])])
            self.log.info("  Command: {}".format(" ".join(glove_cmd)))
            try:
                subprocess.check_call(glove_cmd)
            except subprocess.CalledProcessError as e:
                raise_from(ModuleExecutionError("call to GloVe's glove command failed: {}".format(e)), e)
            glove_output.file_written("vectors.txt")

        # Remove temporary data (the input)
        shutil.rmtree(tmp_dir)

        self.log.info("Training complete: reading in vectors")
        # Read in word counts
        with io.open(vocab_file, "r") as f:
            word_counts = list(_read_word_counts(f))
        # The vectors are already stored sorted by count, in the same order as the vocab
        # Put all the vectors in a numpy array
        vectors = np.zeros((len(word_counts), vector_size), dtype=np.float32)
        with io.open(embeddings_file, "r") as f:
            for i, line in enumerate(islice(f, len(word_counts))):
                line = line.rstrip("\n")
                fields = line.split()
                # Read the word from the first field
                word = fields[0]
                # Check this aligns with the vocab
                if word != word_counts[i][0]:
                    raise ModuleExecutionError("vocab and vector files didn't align: expected '{}' at line '{}', "
                                               "but got '{}'".format(word_counts[i][0], i, word))
                vectors[i, :] = np.array([float(f) for f in fields[1:]])

        self.log.info("Writing out embeddings")
        with self.info.get_output_writer("embeddings") as writer:
            writer.write_word_counts(word_counts)
            writer.write_vectors(vectors)


def _read_word_counts(lines):
    for line in lines:
        line = line.strip("\n")
        word, __, count = line.partition(" ")
        count = int(count)
        yield word, count