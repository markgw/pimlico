from pimlico.core.external.java import Py4JInterface, gateway_client_to_running_server
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.modules.map.multiproc import multiprocessing_executor_factory


@skip_invalid
@invalid_doc_on_error
def process_document(worker, archive, filename, doc):
    return [
        [token.split("\t") for token in sentence]
        for sentence in worker._gateway.entry_point.parseDocFromCoNLLString(doc)
    ]


def preprocess(executor):
    # Initialize the Malt Py4J gateway
    executor.interface = Py4JInterface("pimlico.malt.ParserGateway", gateway_args=[executor.info.model_path],
                                       pipeline=executor.info.pipeline)
    executor.interface.start()
    # Don't parse the CoNLL input data, as we only have to reformat it again
    executor.input_corpora[0].raw_data = True


def postprocess(executor, error=False):
    # Close down the Py4J gateway
    executor.interface.stop()


def worker_set_up(worker):
    # Create a gateway to the single py4j server, which should already be running
    worker._gateway = gateway_client_to_running_server(worker.executor.interface.port_used)


def worker_tear_down(worker):
    worker._gateway.close()


ModuleExecutor = multiprocessing_executor_factory(
    process_document,
    preprocess_fn=preprocess,
    postprocess_fn=postprocess
)
