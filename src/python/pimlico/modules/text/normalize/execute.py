from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def worker_setup(worker):
    worker.case = worker.executor.options["case"]


def process_document(worker, archive_name, doc_name, doc):
    if worker.case == "upper":
        doc = [[word.upper() for word in line] for line in doc]
    elif worker.case == "lower":
        doc = [[word.lower() for word in line] for line in doc]
    return doc


ModuleExecutor = multiprocessing_executor_factory(process_document, worker_set_up_fn=worker_setup)
