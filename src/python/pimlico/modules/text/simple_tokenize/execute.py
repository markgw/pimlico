# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    # We receive plain text input
    # Just split up lines and split each line on spaces (or the given splitter)
    # Also strip whitespace from lines
    # If there are multiple splitters in a row (resulting in empty tokens) ignore them
    sentences = [
        [t for t in line.strip().split(worker.info.options["splitter"]) if len(t)]
        for line in doc.text.splitlines()
    ]
    return dict(sentences=sentences)


ModuleExecutor = multiprocessing_executor_factory(process_document)
