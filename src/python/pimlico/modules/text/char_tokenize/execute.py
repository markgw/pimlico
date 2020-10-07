# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    # We receive plain text input
    # Just split up lines and split lines up into characters
    return worker.info.document(sentences=[list(line) for line in doc.text.splitlines()])


ModuleExecutor = multiprocessing_executor_factory(process_document)
