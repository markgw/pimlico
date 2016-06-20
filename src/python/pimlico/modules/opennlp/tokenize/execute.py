# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
OpenNLP's tokenizer is not thread-safe, so we can't take the approach we use elsewhere of just using one
Py4J gateway with multiple clients. Instead, we start a Py4J gateway in every process.

"""

from pimlico.core.external.java import Py4JInterface
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from .tokenizer import Tokenizer


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Run tokenization
    tokenized_sents = list(worker.tokenizer.tokenize_text(doc))
    # Output one sentence per line
    return u"\n".join(tokenized_sents)


def worker_set_up(worker):
    # Start a tokenizer process running in the background via Py4J
    worker.tokenizer = Tokenizer(worker.info.sentence_model_path, worker.info.token_model_path)
    worker.tokenizer.start()


def worker_tear_down(worker):
    worker.tokenizer.stop()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down,
)
