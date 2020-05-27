# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
OpenNLP's tokenizer is not thread-safe, so we can't take the approach we use elsewhere of just using one
Py4J gateway with multiple clients. Instead, we start a Py4J gateway in every process.

"""
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType
from .tokenizer import Tokenizer


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Run tokenization
    tokenized_sents = list(worker.tokenizer.tokenize_text(doc.text))
    # Output one sentence per line
    return dict(sentences=tokenized_sents)


def executor_set_up(executor):
    # Output to logs whichs models we're using
    if executor.info.options["tokenize_only"]:
        executor.log.info("Tokenizing with model: {}. Not splitting sentences".format(
            executor.info.options["token_model"]
        ))
    else:
        executor.log.info("Tokenizing with model: {}. Sentence splitting with model: {}".format(
            executor.info.options["token_model"], executor.info.options["sentence_model"]
        ))


def worker_set_up(worker):
    # Start a tokenizer process running in the background via Py4J
    worker.tokenizer = Tokenizer(
        None if worker.info.options["tokenize_only"] else worker.info.sentence_model_path,
        worker.info.token_model_path
    )
    worker.tokenizer.start()


def worker_tear_down(worker):
    worker.tokenizer.stop()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down,
    preprocess_fn=executor_set_up,
)
