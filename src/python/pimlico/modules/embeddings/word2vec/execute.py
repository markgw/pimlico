# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from gensim.models.word2vec import Word2Vec
from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.word2vec import Word2VecModel, Word2VecModelWriter
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_corpus = self.info.get_input("text")
        sentences = SentenceIterator(input_corpus)

        self.log.info("Training word2vec on %d documents, %d iterations" %
                      (len(input_corpus), self.info.options["iters"]))
        word2vec = Word2Vec(
            sentences,
            min_count=self.info.options["min_count"],
            size=self.info.options["size"],
            workers=self.processes,
            iter=self.info.options["iters"],
            negative=self.info.options["negative_samples"],
        )
        self.log.info("Training complete: saving model")
        with Word2VecModelWriter(self.info.get_absolute_output_dir("model")) as model:
            model.word2vec_model = word2vec


class SentenceIterator(object):
    def __init__(self, tokenized_corpus):
        self.tokenized_corpus = tokenized_corpus

    def __iter__(self):
        pbar = get_progress_bar(len(self.tokenized_corpus), title="Iterating over sentences", counter=True)
        for doc_name, doc in pbar(self.tokenized_corpus):
            if type(doc) is not InvalidDocument:
                for sentence in doc:
                    yield sentence
