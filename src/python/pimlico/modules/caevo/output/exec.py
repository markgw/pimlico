# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from pimlico.old_datatypes.parse import Tree


@skip_invalid
@invalid_doc_on_error
def process_document(worker, archive, filename, doc):
    # Document is a CaevoDocument, where each entry is a sentence
    # Prepare output data for each of the output writers
    outputs = []
    for output_name in worker.info.output_names:
        if output_name == "tokenized":
            # The Caevo tokenization output is stored as a list of triples, where the word is the middle item of each
            outputs.append([[token[1] for token in entry.tokens] for entry in doc.entries])
        elif output_name == "parse":
            # Caevo just stores the full parse tree as text
            outputs.append([entry.parse or "()" for entry in doc.entries])
        elif output_name == "pos":
            # POS tags aren't provided in a separate field: get them from parse tree
            trees = [Tree.fromstring(entry.parse) for entry in doc.entries]
            tags = [t.pos() for t in trees]
            outputs.append(tags)

    return tuple(outputs)


ModuleExecutor = multiprocessing_executor_factory(process_document)
