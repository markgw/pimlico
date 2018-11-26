# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.cli.browser.tools.formatter import load_formatter
from pimlico.core.modules.base import TypeCheckError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory
from pimlico.datatypes.corpora.data_points import RawTextDocumentType


def worker_setup(worker):
    # Prepare a formatter to format each document
    input_datatype = worker.info.get_input_datatype("corpus")
    try:
        worker.formatter = load_formatter(input_datatype, worker.info.options["formatter"])
    except (TypeError, TypeCheckError), e:
        raise ModuleExecutionError("error loading formatter: %s" % e)


def process_document(worker, archive_name, doc_name, doc):
    return RawTextDocumentType()(text=worker.formatter.format_document(doc))


ModuleExecutor = multiprocessing_executor_factory(process_document, worker_set_up_fn=worker_setup)
