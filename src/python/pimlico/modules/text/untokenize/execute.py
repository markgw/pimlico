from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def process_document(worker, archive_name, doc_name, doc):
    # We receive tokenized input
    # Just join it on spaces (or whatever else has been requested)
    return worker.info.options["sentence_joiner"].join(worker.info.options["joiner"].join(line) for line in doc)


ModuleExecutor = multiprocessing_executor_factory(process_document)
