from collections import Counter

from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def worker_set_up(worker):
    worker.model = worker.info.get_input("model").load_model()


def process_document(worker, archive_name, doc_name, doc):
    # Get a bag of words for the document
    bow = Counter(word for sentence in doc for word in sentence).items()
    # Use the LDA model to infer a topic vector for the document
    vector = worker.model[bow]
    return vector


ModuleExecutor = multiprocessing_executor_factory(process_document, worker_set_up_fn=worker_set_up)
