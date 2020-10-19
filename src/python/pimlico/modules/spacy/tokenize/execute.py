# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.singleproc import single_process_executor_factory
from ..utils import load_spacy_model


def preprocess(executor):
    model = executor.info.options["model"]
    nlp = load_spacy_model(model, executor.log, local=executor.info.options["on_disk"])
    executor.tokenizer = nlp.Defaults.create_tokenizer(nlp)
    executor.sentencizer = nlp.create_pipe("sentencizer")


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Apply tokenization to the raw text
    doc = worker.executor.tokenizer(doc.text)
    # Apply sentence segmentation to the doc
    doc = worker.executor.sentencizer(doc)
    # Now doc.sents contains the separated sentences
    # Filter out any empty sentences or tokens
    sentences = [[token.text for token in sent if len(token.text.strip())] for sent in doc.sents]

    return {"sentences": sentences}


ModuleExecutor = single_process_executor_factory(process_document, preprocess_fn=preprocess)
