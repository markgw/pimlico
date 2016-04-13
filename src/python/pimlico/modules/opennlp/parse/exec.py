from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid
from pimlico.core.parallel.map import MultiprocessingMapProcess, MultiprocessingMapPool, \
    DocumentMapModuleParallelExecutor
from py4j.java_collections import ListConverter


def process_document(doc, gateway):
    """
    Common document processing routine used by parallel and non-parallel versions.

    """
    # Input is a raw string: split on newlines to get tokenized sentences
    sentences = doc.splitlines()
    sentence_list = ListConverter().convert(sentences, gateway._gateway_client)
    # Parse
    return list(gateway.entry_point.parseTrees(sentence_list))


def start_interface(info):
    """
    Start up a Py4J interface to a new JVM.

    """
    # Start a parser process running in the background via Py4J
    interface = Py4JInterface("pimlico.opennlp.ParserGateway", gateway_args=[info.model_path],
                                   pipeline=info.pipeline)
    try:
        interface.start()
    except JavaProcessError, e:
        raise ModuleExecutionError("error starting coref process: %s" % e)
    return interface


class ParseProcess(MultiprocessingMapProcess):
    """
    Each process starts up a separate JVM to make calls to the coref gateway.

    This may seem an unnecessary use of memory, etc, since Py4J is thread-safe and manages connections so that
    we can make multiple asynchronous calls to the same gateway. However, OpenNLP is not thread-safe, so things
    grind to a halt if we do this.

    """
    def set_up(self):
        self.interface = start_interface(self.info)

    def process_document(self, archive, filename, *docs):
        return process_document(docs[0], self.interface.gateway)

    def tear_down(self):
        self.interface.stop()


class ParsePool(MultiprocessingMapPool):
    """
    Simple pool for sending off multiple calls to Py4J at once.

    """
    PROCESS_TYPE = ParseProcess


class ModuleExecutor(DocumentMapModuleParallelExecutor):
    def preprocess(self):
        self.interface = start_interface(self.info)
        # Just get raw data from the input iterator, to skip splitting on spaces and then joining again
        self.input_corpora[0].raw_data = True

    def preprocess_parallel(self):
        # Don't start a Py4J interface in the parallel case, as it's started within the workers
        self.interface = None
        # Don't parse the parse trees, since OpenNLP does that for us, straight from the text
        self.input_corpora[0].raw_data = True

    @skip_invalid
    def process_document(self, archive, filename, doc):
        return process_document(doc, self.interface.gateway)

    def postprocess(self, error=False):
        self.interface.stop()

    def postprocess_parallel(self, error=False):
        # Interface is shut down from threads in parallel case
        self.pool.shutdown()

    def create_pool(self, processes):
        return ParsePool(self, processes)
