from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def process_document(worker, archive_name, doc_name, doc):
    # We receive plain text input
    # Just split up lines and split each line on spaces (or the given splitter)
    # Also strip whitespace from lines
    # If there are multiple splitters in a row (resulting in empty tokens) ignore them
    return [
        [t for t in line.strip().split(worker.info.options["splitter"]) if len(t)]
        for line in doc.splitlines()
    ]


ModuleExecutor = multiprocessing_executor_factory(process_document)
