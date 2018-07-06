# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
from nltk.tokenize.nist import NISTTokenizer
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Run tokenization
    # This tokenizer doesn't split sentences, so we return just a single sentence for each line in the input
    sents = doc.splitlines()
    tokenized_sents = [worker.tokenizer.tokenize(sent, lowercase=worker.info.options["lowercase"]) for sent in sents]
    # Output one sentence per line
    return u"\n".join(u" ".join(sent) for sent in tokenized_sents)


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
