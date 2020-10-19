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

    # Check the order of the fields in the output
    output_dt = worker.info.get_output_datatype("parsed")[1]
    fields_list = output_dt.data_point_type.fields
    # This little function will put the annotations in the right order
    def output(token, pos, head, deprel):
        fields = {"word": token, "pos": pos, "head": head, "deprel": deprel}
        return [fields[field] for field in fields_list]
    worker.output_fields = output


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Apply tagger and parser to the raw text
    doc = worker.nlp(doc.text)
    # Now doc.sents contains the separated sentences
    #  and each word should have a POS tag and head+dep type
    return {
        "word_annotations": [
            [
                worker.output_fields(token.text, token.pos_, str(token.head.i - sentence.start), token.dep_)
                for token in sentence
            ] for sentence in doc.sents
        ]
    }


ModuleExecutor = single_process_executor_factory(process_document, worker_set_up_fn=preprocess)
