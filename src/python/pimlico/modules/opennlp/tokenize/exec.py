"""
OpenNLP's tokenizer is not thread-safe, so we can't take the approach we use elsewhere of just using one
Py4J gateway with multiple clients. Instead, we start a Py4J gateway in every process.

"""

from pimlico.core.external.java import Py4JInterface
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Run tokenization
    tokenized_sents = [sent.decode("utf-8") for sent in worker.gateway.entry_point.tokenize(doc.encode("utf-8"))]
    # Output one sentence per line
    return u"\n".join(tokenized_sents)


def worker_set_up(worker):
    # Start a tokenizer process running in the background via Py4J
    worker.interface = Py4JInterface("pimlico.opennlp.TokenizerGateway",
                                       gateway_args=[worker.info.sentence_model_path, worker.info.token_model_path],
                                       pipeline=worker.info.pipeline, print_stderr=False, print_stdout=False)
    worker.interface.start()
    # Open a client gateway to the executor's py4j interface
    worker.gateway = worker.interface.gateway


def worker_tear_down(worker):
    worker.interface.stop()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down,
)
