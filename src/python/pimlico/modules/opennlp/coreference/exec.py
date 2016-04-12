"""
TODO I've tried to parellelize this. It helps if the number of processes is low (e.g. 3), but for higher (e.g. 10)
it gets horrible. Something's wrong. It could just be java consuming tonnes of memory.
"""

from Queue import Queue, Empty
from threading import Thread, Event
from traceback import format_exc

from pimlico.core.external.java import Py4JInterface, JavaProcessError
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import skip_invalid
from pimlico.core.parallel.map import ProcessOutput, DocumentProcessorPool, DocumentMapModuleParallelExecutor
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.coref.opennlp import Entity
from pimlico.modules.opennlp.coreference.info import WORDNET_DIR
from py4j.java_collections import ListConverter


def process_document(doc, gateway):
    # Input is a list of parse trees: split them up (into sentences)
    tree_strings = doc.split("\n\n")
    # Convert Python list to Java list
    parse_list = ListConverter().convert(tree_strings, gateway._gateway_client)
    # Resolve coreference, passing in PTB parse trees as strings
    coref_output = list(gateway.entry_point.resolveCoreferenceFromTrees(parse_list))
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
        java_opts=["-Xmx500M"]
    )
    try:
        interface.start()
    except JavaProcessError, e:
        raise ModuleExecutionError("error starting coref process: %s" % e)
    return interface


class CorefThread(Thread):
    """
    Each thread starts up a separate JVM to make calls to the coref gateway.

    This may seem an unnecessary use of memory, etc, since Py4J is thread-safe and manages connections so that
    we can make multiple asynchronous calls to the same gateway. However, OpenNLP is not thread-safe, so things
    grind to a halt if we do this.

    """
    def __init__(self, input_queue, output_queue, info):
        super(CorefThread, self).__init__()
        self.info = info
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True
        self.stopped = Event()

        # Start a Java process running in the background via Py4J: we'll send all our jobs to this
        self.interface = start_interface(self.info)
        self.start()

    def run(self):
        try:
            while not self.stopped.is_set():
                try:
                    archive, filename, doc = self.input_queue.get(False, 0.1)
                    try:
                        result = process_document(doc, self.interface.gateway)
                        self.output_queue.put(ProcessOutput(archive, filename, result))
                    except Exception, e:
                        self.output_queue.put(
                            ProcessOutput(archive, filename, InvalidDocument(self.info.module_name,
                                                                             "%s\n%s" % (e, format_exc())))
                        )
                    finally:
                        self.input_queue.task_done()
                except Empty:
                    # Don't worry if the queue is empty: just keep waiting for more until we're shut down
                    pass
        finally:
            # Close down the Py74J server once we're done
            self.interface.stop()


class CorefPool(DocumentProcessorPool):
    """
    Simple pool for sending off multiple calls to Py4J at once. It doesn't use multiprocessing --
    threaded calls to Py4J fire off separate processes on the Java side, so it just does this.

    """
    def __init__(self, executor, processes):
        super(CorefPool, self).__init__(processes)
        self.executor = executor
        self.input_queue = Queue()
        self.workers = [CorefThread(self.input_queue, self.queue, self.executor.info) for i in range(processes)]

    @staticmethod
    def create_queue():
        # Don't need a multiprocessing queue, since we only use threading
        return Queue()

    def process_document(self, archive, filename, doc):
        # Put the document on the queue and let the worker processes get on with it
        self.input_queue.put((archive, filename, doc))

    def shutdown(self):
        # Clear the input queue
        try:
            while not self.input_queue.empty():
                self.input_queue.get_nowait()
        except Empty:
            pass
        # Tell all the threads to stop
        for worker in self.workers:
            worker.stopped.set()
        # Wait until they've all stopped
        for worker in self.workers:
            worker.join()


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
        # Py4J server has already been set going by preprocess()
        return CorefPool(self, processes)
