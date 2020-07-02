import re

from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


def worker_setup(worker):
    worker.case = worker.executor.info.options["case"]
    worker.remove_empty = worker.executor.info.options["remove_empty"]
    worker.remove_only_punct = worker.executor.info.options["remove_only_punct"]
    worker.remove_punct = worker.executor.info.options["remove_punct"]
    worker.min_word_length = worker.executor.info.options["min_word_length"]
    worker.remove_nums = worker.executor.info.options["remove_nums"]


only_punct_re = re.compile(r"[^\W_]*$")
punct_re = re.compile(r"[\W_]")
num_re = re.compile(r"[0-9]")


def process_document(worker, archive_name, doc_name, doc):
    sentences = doc.sentences

    if worker.case == "upper":
        sentences = [[word.upper() for word in sentence] for sentence in sentences]
    elif worker.case == "lower":
        sentences = [[word.lower() for word in sentence] for sentence in sentences]

    if worker.remove_punct:
        # Remove all punctuation from all words
        sentences = [
            [punct_re.sub("", word).strip() for word in sentence] for sentence in sentences
        ]

    if worker.remove_only_punct:
        sentences = [sentence for sentence in sentences if not all(only_punct_re.match(w) for w in sentence)]

    if worker.remove_nums:
        sentences = [[num_re.sub("", word) for word in sentence] for sentence in sentences]

    if worker.min_word_length > 0:
        sentences = [
            [word for word in sentence if len(word) > worker.min_word_length] for sentence in sentences
        ]

    # Drop any words that have nothing left
    sentences = [[word for word in sentence if len(word)] for sentence in sentences]
    if worker.remove_empty:
        # Drop any sentences that have nothing left
        sentences = [sentence for sentence in sentences if len(sentence)]

    return dict(sentences=sentences)


ModuleExecutor = multiprocessing_executor_factory(process_document, worker_set_up_fn=worker_setup)
