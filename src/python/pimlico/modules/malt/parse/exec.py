import Queue
from threading import Thread

from pimlico.core.external.java import Py4JInterface
from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.core.parallel.map import DocumentMapModuleParallelExecutor, DocumentProcessorPool
from py4j.java_collections import ListConverter


def process_document(archive, filename, doc, gateway):
    # Split up sentences
    # TODO This isn't working: debug
    sentences = [
        "\n".split(sentence) for sentence in "\n\n".split(doc)
    ]
    sentence_list = ListConverter().convert(sentences, gateway._gateway_client)
    return list(gateway.entry_point.parseFromCoNLL(sentence_list))


class MaltWorkerThread(Thread):
    def __init__(self, gateway, input_queue, output_queue):
        super(MaltWorkerThread, self).__init__()
        self.output_queue = output_queue
        self.input_queue = input_queue
        self.gateway = gateway

    def run(self):
        # Wait for an input from the queue
        new_input = self.input_queue.get()
        if new_input is None:
            # No more inputs to come: time to shut down
            return
        else:
            archive, filename, doc = new_input
            result = process_document(archive, filename, doc, self.gateway)
            # Put the result on the output queue
            self.output_queue.put((archive, filename, result))
            # Indicate that we're done
            self.input_queue.task_complete()


class MaltPool(DocumentProcessorPool):
    """
    Simple pool for sending off multiple calls to the Py4J gateway at once. It doesn't use multiprocessing, since
    the Py4J gateway fires off multiple Java threads for multiple requests. It just uses threading to send non-blocking
    requests to the gateway.

    """
    # TODO Parallel processing hangs at startup: debug
    def __init__(self, executor, processes):
        super(MaltPool, self).__init__(processes)
        self.executor = executor
        self.input_queue = Queue.Queue()
        # Create the number of workers we need to send requests to Malt and wait for results
        self.workers = [
            MaltWorkerThread(self.executor.interface.gateway, self.input_queue, self.queue) for i in range(processes)
        ]

    @staticmethod
    def create_queue():
        # Don't need a multiprocessing queue, since we only use threading
        return Queue.Queue()

    @skip_invalid
    def process_document(self, archive, filename, doc):
        # Send the doc to the input queue to be picked up by one of the threads
        self.input_queue.put((archive, filename, doc))

    def shutdown(self):
        # Clear the input queue, if there's anything waiting to be processed
        while not self.input_queue.empty():
            self.input_queue.get_nowait()
        # Put a None in the input queue for each thread to tell it to shut down
        for i in range(len(self.workers)):
            self.input_queue.put(None)
        # Wait for all threads to finish
        for worker in self.workers:
            worker.join()


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
