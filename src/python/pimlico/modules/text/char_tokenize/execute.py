from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    # We receive plain text input
    # Just split up lines and split lines up into characters
    return [list(line) for line in doc.splitlines()]


ModuleExecutor = multiprocessing_executor_factory(process_document)
