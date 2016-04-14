from pimlico.core.external.java import Py4JInterface, gateway_client_to_running_server
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.parallel.map import DocumentMapModuleParallelExecutor, MultiprocessingMapPool, \
    MultiprocessingMapProcess


def process_document(archive, filename, doc, gateway):
    return [
        [token.split("\t") for token in sentence]
        for sentence in gateway.entry_point.parseDocFromCoNLLString(doc)
    ]


class MaltWorkerProcess(MultiprocessingMapProcess):
    def __init__(self, input_queue, output_queue, info, py4j_port):
        self._gateway = None
        self.py4j_port = py4j_port
        super(MaltWorkerProcess, self).__init__(input_queue, output_queue, info)

    def set_up(self):
        self._gateway = gateway_client_to_running_server(self.py4j_port)

    def process_document(self, archive, filename, *docs):
        return process_document(archive, filename, docs[0], self._gateway)

    def tear_down(self):
        self._gateway.close()


class MaltPool(MultiprocessingMapPool):
    """
    Simple pool for sending off multiple calls to the Py4J gateway at once. It doesn't use multiprocessing, since
    the Py4J gateway fires off multiple Java threads for multiple requests. It just uses threading to send non-blocking
    requests to the gateway.

    """
    def start_worker(self):
        return MaltWorkerProcess(self.input_queue, self.output_queue,
                                 self.executor.info, self.executor.interface.port_used)


class ModuleExecutor(DocumentMapModuleParallelExecutor):
    def preprocess(self):
        # Initialize the Malt Py4J gateway
        self.interface = Py4JInterface("pimlico.malt.ParserGateway", gateway_args=[self.info.model_path],
                                       pipeline=self.info.pipeline)
        self.interface.start()
        # Don't parse the CoNLL input data, as we only have to reformat it again
        self.input_corpora[0].raw_data = True

    def create_pool(self, processes):
        # CoreNLP server has already been set going by preprocess()
        return MaltPool(self, processes)

    @skip_invalid
    @invalid_doc_on_error
    def process_document(self, archive, filename, doc):
        return process_document(archive, filename, doc, self.interface.gateway)

    def postprocess_parallel(self, error=False):
        self.pool.shutdown()
        # Close down the Py4J gateway
        self.interface.stop()
