import re
import string

from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def worker_setup(worker):
    worker.case = worker.executor.info.options["case"]
    worker.remove_empty = worker.executor.info.options["remove_empty"]
    worker.remove_only_punct = worker.executor.info.options["remove_only_punct"]


only_punct_re = re.compile(r"[{}]*$".format(string.punctuation))


def process_document(worker, archive_name, doc_name, doc):
    sentences = doc.sentences
    if worker.case == "upper":
        sentences = [[word.upper() for word in sentence] for sentence in sentences]
    elif worker.case == "lower":
        sentences = [[word.lower() for word in sentence] for sentence in sentences]

    if worker.remove_empty:
        sentences = [sentence for sentence in sentences if len(sentence) > 0]

    if worker.remove_only_punct:
        sentences = [sentence for sentence in sentences if not all(only_punct_re.match(w) for w in sentence)]

    return dict(sentences=sentences)


ModuleExecutor = multiprocessing_executor_factory(process_document, worker_set_up_fn=worker_setup)
