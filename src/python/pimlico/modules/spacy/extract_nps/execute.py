# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.singleproc import single_process_executor_factory
from ..utils import load_spacy_model


def preprocess(worker):
    model = worker.info.options["model"]
    nlp = load_spacy_model(model, worker.executor.log, local=worker.info.options["on_disk"])

    pipeline = ["tagger", "parser"]
    for pipe_name in nlp.pipe_names:
        if pipe_name not in pipeline:
            # Remove any components other than the tagger and parser that might be in the model
            nlp.remove_pipe(pipe_name)
    worker.nlp = nlp


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Apply tagger and parser to the raw text
    doc = worker.nlp(doc.text)
    # Now doc.noun_chunks contains the NP chunks from the parser
    return {
        "sentences": [[token.text for token in np] for np in doc.noun_chunks]
    }


ModuleExecutor = single_process_executor_factory(process_document, worker_set_up_fn=preprocess)
