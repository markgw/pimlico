from pimlico.core.external.java import Py4JInterface, gateway_client_to_running_server
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.parallel.map import DocumentMapModuleParallelExecutor, MultiprocessingMapPool, \
    MultiprocessingMapProcess


def process_document(archive, filename, doc, gateway):
    # TODO This is not suitable input to the parser, since it needs supertags (and POS tags)
    return "\n\n".join(gateway.entry_point.parse("\n\n".join("\n".join(word for word in sentence) for sentence in doc)))


class CandcWorkerProcess(MultiprocessingMapProcess):
    def __init__(self, input_queue, output_queue, info, py4j_port):
        self._gateway = None
        self.py4j_port = py4j_port
        super(CandcWorkerProcess, self).__init__(input_queue, output_queue, info)

    def set_up(self):
        self._gateway = gateway_client_to_running_server(self.py4j_port)

    def process_document(self, archive, filename, *docs):
        return process_document(archive, filename, docs[0], self._gateway)

    def tear_down(self):
        self._gateway.close()


class CandcPool(MultiprocessingMapPool):
    """
    Simple pool for sending off multiple calls to the Py4J gateway at once.

    """
    def start_worker(self):
        return CandcWorkerProcess(self.input_queue, self.output_queue,
                                  self.executor.info, self.executor.interface.port_used)


class ModuleExecutor(DocumentMapModuleParallelExecutor):
    def preprocess(self):
        # Initialize the C&C Py4J gateway
        gateway_args = [self.info.model_path, self.info.grammar_dir, self.info.lexicon_path, self.info.features_path]
        if self.info.params_path:
            gateway_args.extend(["--params", self.info.params_path])
        self.log.info("Starting up the C&C parser: this can take a couple of minutes")
        self.interface = Py4JInterface(
            "pimlico.candc.CandcGateway", gateway_args=gateway_args, pipeline=self.info.pipeline,
            print_stderr=False, print_stdout=False)
        # Use a longer timeout than usual, because C&C takes ages to load
        # Since C&C outputs stuff to stdout, we use a special prefix to denote the port number
        self.interface.start(timeout=120., port_output_prefix="PORT ")

    def create_pool(self, processes):
        return CandcPool(self, processes)

    @skip_invalid
    @invalid_doc_on_error
    def process_document(self, archive, filename, doc):
        return process_document(archive, filename, doc, self.interface.gateway)

    def postprocess_parallel(self, error=False):
        self.pool.shutdown()
        # Close down the Py4J gateway
        self.interface.stop()
