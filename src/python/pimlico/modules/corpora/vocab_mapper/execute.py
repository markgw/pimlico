# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def preprocess(executor):
    # Load the dictionary
    executor.vocab = executor.info.get_input("vocab").get_data()


def process_document(worker, archive_name, doc_name, doc):
    vocab = worker.executor.vocab

    oov_token = worker.info.options["oov"]
    if oov_token is not None:
        oov = vocab.token2id[oov_token]
    else:
        # Use the next unused ID after the vocab to represent OOV words
        oov = len(vocab)

    # Map all words to their IDs, or OOV if they're not in the vocab
    int_data = [
        [vocab.token2id[word] if word in vocab.token2id else oov for word in sentence] for sentence in doc
    ]
    return int_data


ModuleExecutor = multiprocessing_executor_factory(process_document, preprocess_fn=preprocess)
