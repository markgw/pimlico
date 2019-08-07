# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from builtins import zip
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from pimlico.old_datatypes.word_annotations import WordAnnotationCorpus
from .ner import NERTagger


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Input is a list of tokenized sentences, which may have other tags too
    if len(doc):
        # Check whether this is dicts of annotations or just tokens
        if worker.input_fields:
            input_words = [[word["word"] for word in sentence] for sentence in doc]
        else:
            input_words = doc
        # Run NER
        spans = worker.tagger.tag_sentences(input_words)
        # Put the NER tags together with the annotations we've already got
        # The writer will format them to look like word|NER
        return list(zip(input_words, spans))
    else:
        return []


def worker_set_up(worker):
    # Check that the input provides us with words
    if isinstance(worker.executor.input_corpora[0], WordAnnotationCorpus):
        available_fields = worker.executor.input_corpora[0].read_annotation_fields()
        if "word" not in available_fields:
            raise ModuleExecutionError("input datatype does not provide a field 'word' -- can't POS tag it")
        worker.input_fields = True
    else:
        worker.input_fields = False
    # Start a tokenizer process running in the background via Py4J
    worker.tagger = NERTagger(worker.info.model_path, pipeline=worker.info.pipeline)
    worker.tagger.start()


def worker_tear_down(worker):
    worker.tagger.stop()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down
)
