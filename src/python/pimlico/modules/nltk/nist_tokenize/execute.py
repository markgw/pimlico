# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from nltk.tokenize.nist import NISTTokenizer
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Run tokenization
    # This tokenizer doesn't split sentences, so linebreaks will be the same as in the input
    # These linebreaks will subsequently be treated as sentence breaks
    tokenized_text = worker.tokenizer.tokenize(doc.text, lowercase=worker.info.options["lowercase"], return_str=True)
    sentences = [sent.split(" ") for sent in tokenized_text.splitlines()]
    return worker.info.document(sentences=sentences)


def worker_set_up(worker):
    # Prepare a tokenizer
    worker.tokenizer = NISTTokenizer()
    if worker.info.options["non_european"]:
        worker.tokenize = worker.tokenizer.international_tokenize
    else:
        worker.tokenize = worker.tokenizer.tokenize


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    worker_set_up_fn=worker_set_up,
)
