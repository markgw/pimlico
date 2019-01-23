# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from gensim.models.word2vec import Word2Vec

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.corpora import is_invalid_doc
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_corpus = self.info.get_input("text")
        sentences = SentenceIterator(input_corpus)

        self.log.info("Training word2vec on {:,d} documents, {:d} iterations using Gensim".format(
            len(input_corpus), self.info.options["iters"]
        ))
        if self.processes > 1:
            self.log.info("Using {:d} worker processes".format(self.processes))

        # Run training
        word2vec = Word2Vec(
            sentences,
            min_count=self.info.options["min_count"],
            size=self.info.options["size"],
            workers=self.processes,
            iter=self.info.options["iters"],
            negative=self.info.options["negative_samples"],
        )
        self.log.info("Training complete. Trained {:,d} vectors".format(word2vec.wv.vectors.shape[0]))
        self.log.info("Writing out vectors")
        with self.info.get_output_writer("model") as writer:
            writer.write_keyed_vectors(word2vec.wv)


class SentenceIterator(object):
    def __init__(self, tokenized_corpus):
        self.tokenized_corpus = tokenized_corpus

    def __iter__(self):
        pbar = get_progress_bar(len(self.tokenized_corpus), title="Iterating over sentences", counter=True)
        for doc_name, doc in pbar(self.tokenized_corpus):
            if not is_invalid_doc(doc):
                for sentence in doc.sentences:
                    yield sentence
