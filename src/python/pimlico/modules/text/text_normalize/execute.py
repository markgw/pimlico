from pimlico.core.modules.map import skip_invalid

from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def worker_setup(worker):
    worker.case = worker.executor.info.options["case"]
    worker.strip = worker.executor.info.options["strip"]
    worker.blank_lines = worker.executor.info.options["blank_lines"]


@skip_invalid
def process_document(worker, archive_name, doc_name, doc):
    # First split into lines, since much works on the line level
    lines = doc.text.splitlines()

    if worker.case == "upper":
        lines = [line.upper() for line in lines]
    elif worker.case == "lower":
        lines = [line.lower() for line in lines]

    if worker.strip:
        lines = [line.strip() for line in lines]

    if worker.blank_lines:
        lines = [l for l in lines if len(l) > 0]

    return worker.info.document(text=u"\n".join(lines))


ModuleExecutor = multiprocessing_executor_factory(process_document, worker_set_up_fn=worker_setup)
