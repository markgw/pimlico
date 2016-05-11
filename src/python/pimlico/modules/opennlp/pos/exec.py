# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.external.java import Py4JInterface, gateway_client_to_running_server
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from pimlico.datatypes.word_annotations import WordAnnotationCorpus
from py4j.java_collections import ListConverter


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Input is a list of tokenized sentences
    # Run POS tagging
    sentence_list = ListConverter().convert(
        [" ".join(sentence) for sentence in doc],
        worker.gateway._gateway_client
    )
    tags = list(worker.gateway.entry_point.posTag(sentence_list))
    # Put the POS tags together with the words
    # The writer will format them to look like word|POS
    return [
        zip(sentence_words, sentence_tags.split())
        for (sentence_words, sentence_tags) in zip(doc, tags)
    ]


def worker_set_up(worker):
    # Check that the input provides us with words
    if isinstance(worker.executor.input_corpora[0], WordAnnotationCorpus):
        available_fields = worker.executor.input_corpora[0].read_annotation_fields()
        if "word" not in available_fields:
            raise ModuleExecutionError("input datatype does not provide a field 'word' -- can't POS tag it")
    # Start a tokenizer process running in the background via Py4J
    worker.interface = Py4JInterface("pimlico.opennlp.PosTaggerGateway", gateway_args=[worker.info.model_path],
                                     pipeline=worker.info.pipeline, print_stderr=False, print_stdout=False)
    worker.interface.start()
    worker.gateway = worker.interface.gateway


def worker_tear_down(worker):
    worker.interface.stop()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down
)
