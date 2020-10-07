# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def preprocess(executor):
    # Load the dictionary
    executor.vocab = executor.info.get_input("vocab").get_data()
    id2token = executor.vocab.id2token

    oov_token = executor.info.options["oov"]
    if oov_token == "skip":
        # A mapping to None signals that this word should be skipped
        id2token[len(executor.vocab)] = None
    elif oov_token is not None:
        id2token[len(executor.vocab)] = oov_token
    # Otherwise we add no special mapping for OOVs

    executor.id2token = id2token


@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    id2token = worker.executor.id2token

    doc_tokens = [
        [id2token[i] for i in sent if id2token[i] is not None] for sent in doc.lists
    ]
    return {"sentences": doc_tokens}


ModuleExecutor = multiprocessing_executor_factory(process_document, preprocess_fn=preprocess)
