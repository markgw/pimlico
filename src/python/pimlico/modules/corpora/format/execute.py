# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.cli.browser.tools.formatter import load_formatter
from pimlico.core.modules.base import TypeCheckError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from pimlico.datatypes.corpora.data_points import RawTextDocumentType


def worker_setup(worker):
    # Prepare a formatter to format each document
    input_datatype = worker.info.get_input_datatype("corpus")
    try:
        worker.formatter = load_formatter(input_datatype, worker.info.options["formatter"])
    except (TypeError, TypeCheckError) as e:
        raise ModuleExecutionError("error loading formatter: %s" % e)


@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    return RawTextDocumentType()(text=worker.formatter.format_document(doc))


ModuleExecutor = multiprocessing_executor_factory(process_document, worker_set_up_fn=worker_setup)
