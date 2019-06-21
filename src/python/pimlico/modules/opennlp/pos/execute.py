# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from builtins import zip
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from pimlico.old_datatypes.word_annotations import WordAnnotationCorpus
from .tagger import PosTagger


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Input is a list of tokenized sentences
    # Run POS tagging
    tags = worker.tagger.tag_sentences(doc)
    # Filter out any |s from the words, as they'll destroy out output format
    words = [[word.replace("|", "") for word in sentence] for sentence in doc]
    # Put the POS tags together with the words
    # The writer will format them to look like word|POS
    return [
        list(zip(sentence_words, sentence_tags))
        for (sentence_words, sentence_tags) in zip(words, tags)
    ]


def worker_set_up(worker):
    # Check that the input provides us with words
    if isinstance(worker.executor.input_corpora[0], WordAnnotationCorpus):
        available_fields = worker.executor.input_corpora[0].read_annotation_fields()
        if "word" not in available_fields:
            raise ModuleExecutionError("input datatype does not provide a field 'word' -- can't POS tag it")
    # Start a tokenizer process running in the background via Py4J
    worker.tagger = PosTagger(worker.info.model_path, pipeline=worker.info.pipeline)
    worker.tagger.start()


def worker_tear_down(worker):
    worker.tagger.stop()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down
)
