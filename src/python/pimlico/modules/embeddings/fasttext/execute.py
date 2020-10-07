# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

import os
from collections import Counter
from io import open

import fasttext
import numpy as np

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_corpus = self.info.get_input("text")
        opts = self.info.options

        input_path = os.path.join(self.info.get_module_output_dir(absolute=True), "fasttext_input_data.txt")
        self.log.info("Preparing input data file for fastText: {}".format(input_path))
        pbar = get_progress_bar(len(input_corpus), title="Preparing data")

        # Fasttext needs to read its input from a unicode text file, so we output the corpus
        # We'll also keep word counts at the same time, for writing plain embeddings later
        word_counts = Counter()
        with open(input_path, "w", encoding="utf-8") as f:
            for doc_name, doc in pbar(input_corpus):
                for sentence in doc.sentences:
                    f.write(u"{}\n".format(u" ".join(sentence)))
                    word_counts.update(sentence)

        self.log.info("Training fastText embeddings")
        # Almost all options come straight from the module options
        model = fasttext.train_unsupervised(
            input_path,
            model=opts["model"],
            lr=opts["lr"],
            dim=opts["dim"],
            ws=opts["ws"],
            epoch=opts["epoch"],
            minCount=opts["min_count"],
            minn=opts["minn"], maxn=opts["maxn"],
            neg=opts["neg"],
            wordNgrams=opts["word_ngrams"],
            loss=opts["loss"],
            bucket=opts["bucket"],
            thread=self.processes,
            lrUpdateRate=opts["lr_update_rate"],
            t=opts["t"],
            verbose=opts["verbose"],
        )

        num_words = len(model.words)
        self.log.info("Training complete. Trained {:,d} vectors".format(num_words))

        self.log.info("Writing out fastText embeddings in native fastText format")
        with self.info.get_output_writer("model") as writer:
            writer.save_model(model)

        self.log.info("Writing out plain embeddings")
        with self.info.get_output_writer("embeddings") as writer:
            # Build a dictionary of word counts for all the words for which embeddings are stored
            model_word_counts = [(word, word_counts[word]) for word in model.words]
            writer.write_word_counts(model_word_counts)
            # Now get the embeddings in one big matrix
            vectors = np.zeros((len(model.words), model.dim), dtype=np.float32)
            for w, word in enumerate(model.words):
                vectors[w] = model[word]
            # Output the vectors
            writer.write_vectors(vectors)
