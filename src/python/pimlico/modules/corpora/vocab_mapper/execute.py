# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def preprocess(executor):
    # Load the dictionary
    executor.vocab = executor.info.get_input("vocab").get_data()
    oov_token = executor.info.options["oov"]
    if oov_token == "skip":
        oov = None
    elif oov_token is not None:
        oov = executor.vocab.token2id[oov_token]
    else:
        # Use the next unused ID after the vocab to represent OOV words
        oov = len(executor.vocab)
    executor.oov = oov


@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    vocab = worker.executor.vocab
    oov = worker.executor.oov

    if oov is None:
        # Special value that causes us to skip over OOVs
        doc_ids = [[vocab.token2id[word] for word in words if word in vocab.token2id] for words in doc.sentences]
        # Skip empty sentences (which may have come from sentences with only OOVs)
        lsts = [sent for sent in doc_ids if len(sent)]
    else:
        # Map all words to their IDs, or OOV if they're not in the vocab
        lsts = [[vocab.token2id[word] if word in vocab.token2id else oov for word in words] for words in doc.sentences]
    return worker.info.document(lists=lsts)


ModuleExecutor = multiprocessing_executor_factory(process_document, preprocess_fn=preprocess)
