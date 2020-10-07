# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from builtins import zip

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from .tagger import PosTagger


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Input is a list of tokenized sentences
    # Run POS tagging
    tags = worker.tagger.tag_sentences(doc.sentences)
    # Put the POS tags together with the words
    return {
        "word_annotations": [
            list(zip(sentence_words, sentence_tags))
            for (sentence_words, sentence_tags) in zip(doc.sentences, tags)
        ]
    }


def worker_set_up(worker):
    # Start a tokenizer process running in the background via Py4J
    worker.tagger = PosTagger(worker.info.model_path, pipeline=worker.info.pipeline)
    worker.tagger.start()


def worker_tear_down(worker):
    worker.tagger.stop()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down
)
