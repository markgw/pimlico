from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid
from pimlico.core.parallel.map import DocumentMapModuleParallelExecutor, \
    MultiprocessingMapProcess, MultiprocessingMapPool
from pimlico.datatypes.coref.opennlp import Entity
from pimlico.modules.opennlp.coreference.info import WORDNET_DIR


def process_document(doc, gateway):
    """
    Common document processing routine used by parallel and non-parallel versions.

    """
    # Resolve coreference, passing in PTB parse trees as strings
    coref_output = list(gateway.entry_point.resolveCoreferenceFromTreesStrings(doc))
    # Pull all of the information out of the java objects to get ready to store as JSON
    entities = [Entity.from_java_object(e) for e in coref_output]
    return entities


def start_interface(info):
    """
    Start up a Py4J interface to a new JVM.

    """
    interface = Py4JInterface(
        "pimlico.opennlp.CoreferenceResolverGateway", gateway_args=[info.model_path],
        pipeline=info.pipeline, system_properties={"WNSEARCHDIR": WORDNET_DIR},
        java_opts=["-Xmx%s" % info.get_heap_memory_limit(), "-Xms%s" % info.get_heap_memory_limit()]
    )
    try:
        interface.start()
    except JavaProcessError, e:
        raise ModuleExecutionError("error starting coref process: %s" % e)
    return interface


class CorefProcess(MultiprocessingMapProcess):
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


class CorefPool(MultiprocessingMapPool):
    """
    Simple pool for sending off multiple calls to Py4J at once. We use multiprocessing, since there's some
    postprocessing to be done for each doc after it comes back from Py4J, so if you just use threads they end
    up getting in each others' way so that it doesn't go any faster than if you used far fewer (applies > ~3
    threads).

    """
    PROCESS_TYPE = CorefProcess


class ModuleExecutor(DocumentMapModuleParallelExecutor):
    def preprocess(self):
        # Start a Java process running in the background via Py4J
        self.interface = start_interface(self.info)
        # Don't parse the parse trees, since OpenNLP does that for us, straight from the text
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
        self.interface = None

    def postprocess_parallel(self, error=False):
        # Interface is shut down from threads in parallel case
        self.pool.shutdown()

    def create_pool(self, processes):
        return CorefPool(self, processes)
