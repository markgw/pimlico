from pimlico.core.external.java import Py4JInterface, gateway_client_to_running_server
from pimlico.core.modules.map import skip_invalid
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
def process_document(worker, archive, filename, doc):
    # Run tokenization
    tokenized_sents = list(worker.gateway.entry_point.tokenize(doc))
    # Output one sentence per line
    return u"\n".join(tokenized_sents)


def preprocess(executor):
    # Start a tokenizer process running in the background via Py4J
    executor.interface = Py4JInterface("pimlico.opennlp.TokenizerGateway",
                                       gateway_args=[executor.info.sentence_model_path, executor.info.token_model_path],
                                       pipeline=executor.info.pipeline, print_stderr=False, print_stdout=False)
    executor.interface.start()
    executor.gateway_port = executor.interface.port_used


def postprocess(executor, error=False):
    executor.interface.stop()


def worker_set_up(worker):
    # Open a client gateway to the executor's py4j interface
    worker.gateway = gateway_client_to_running_server(worker.executor.gateway_port)


def worker_tear_down(worker):
    worker.gateway.close()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    preprocess_fn=preprocess, postprocess_fn=postprocess,
    worker_set_up_fn=worker_set_up, worker_tear_down_fn=worker_tear_down,
)
