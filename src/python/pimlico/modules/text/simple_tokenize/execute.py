from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def process_document(worker, archive_name, doc_name, doc):
    # We receive plain text input
    # Just split up lines and split each line on spaces (or the given splitter)
    # Also strip whitespace from lines
    return [
        line.strip().split(worker.info.options["splitter"])
        for line in doc.splitlines()
    ]


ModuleExecutor = multiprocessing_executor_factory(process_document)
