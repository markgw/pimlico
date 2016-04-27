"""
Sometimes the simple multiprocessing-based approach to map module parallelization just isn't suitable.
This module provides an equivalent set of implementations and convenience functions that don't use
multiprocessing, but conform to the pool-based execution pattern by creating a single-thread pool.

"""
import threading
from Queue import Queue, Empty
from traceback import format_exc

from pimlico.core.modules.map import DocumentMapProcessMixin, ProcessOutput, DocumentProcessorPool, \
    DocumentMapModuleExecutor
from pimlico.datatypes.base import InvalidDocument


class SingleThreadMapWorker(threading.Thread, DocumentMapProcessMixin):
    def __init__(self, input_queue, output_queue, executor):
        threading.Thread.__init__(self)
        DocumentMapProcessMixin.__init__(self)
        self.executor = executor
        self.info = executor.info
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True
        self.stopped = threading.Event()
        self.initialized = threading.Event()
        self.uncaught_exception = Queue(1)

        self.start()

    def run(self):
        try:
            # Run any startup routine that the subclass has defined
            self.set_up()
            # Notify waiting processes that we've finished initialization
            self.initialized.set()
            try:
                while not self.stopped.is_set():
                    try:
                        # Timeout and go round the loop again to check whether we're supposed to have stopped
                        archive, filename, docs = self.input_queue.get(timeout=0.05)
                        try:
                            result = self.process_document(archive, filename, *docs)
                        except Exception, e:
                            self.output_queue.put(
                                ProcessOutput(archive, filename, InvalidDocument(self.info.module_name,
                                                                                 "%s\n%s" % (e, format_exc())))
                            )
                        else:
                            self.output_queue.put(ProcessOutput(archive, filename, result))
                    except Empty:
                        # Don't worry if the queue is empty: just keep waiting for more until we're shut down
                        pass
            finally:
                self.tear_down()
        except Exception, e:
            # If there's any uncaught exception, make it available to the main process
            self.uncaught_exception.put_nowait(e)
        finally:
            # Even there was an error, set initialized so that the main process can wait on it
            self.initialized.set()


class SingleThreadMapPool(DocumentProcessorPool):
    """
    A base implementation of document map parallelization using multiprocessing.

    """
    THREAD_TYPE = None

    def __init__(self, executor):
        super(SingleThreadMapPool, self).__init__(1)
        self.executor = executor
        self.worker = self.start_worker()
        # Wait until all of the workers have completed their initialization
        self.worker.initialized.wait()
        # Check whether the worker had an error during initialization
        try:
            e = self.worker.uncaught_exception.get_nowait()
        except Empty:
            # No error
            pass
        else:
            raise WorkerStartupError("error in worker thread: %s" % e, cause=e)

    def start_worker(self):
        return self.THREAD_TYPE(self.input_queue, self.output_queue, self.executor)

    @staticmethod
    def create_input_queue(size):
        return Queue(size)

    @staticmethod
    def create_output_queue():
        return Queue()

    def shutdown(self):
        # Tell the thread to stop
        self.worker.stopped.set()
        # Wait until it's stopped
        while self.worker.is_alive():
            # Need to clear the output queue, or else the join hangs
            while not self.output_queue.empty():
                self.output_queue.get_nowait()
            self.worker.join(0.1)


class MultiprocessingMapModuleExecutor(DocumentMapModuleExecutor):
    POOL_TYPE = None

    def create_pool(self, processes):
        return self.POOL_TYPE(self, processes)

    def postprocess(self, error=False):
        self.pool.shutdown()


def single_process_executor_factory(process_document_fn, preprocess_fn=None, postprocess_fn=None):
    """
    Factory function for creating an executor that uses the single-process implementations of document-map
    pools and workers. This is an easy way to implement a non-parallelized executor

    process_document_fn should be a function that takes the following arguments:

    - the executor instance (allowing access to things set during setup)
    - archive name
    - document name
    - the rest of the args are the document itself, from each of the input corpora

    If proprocess_fn is given, it is called once before execution begins, with the executor as an argument.

    If postprocess_fn is given, it is called at the end of execution, including on the way out after an error,
    with the executor as an argument and a kwarg *error* which is True if execution failed.

    """
    # Define a worker thread type
    class FactoryMadeMapThread(SingleThreadMapWorker):
        def process_document(self, archive, filename, *docs):
            process_document_fn(self.executor, archive, filename, *docs)

    # Define a pool type to use this worker thread type
    class FactoryMadeMapPool(SingleThreadMapPool):
        PROCESS_TYPE = FactoryMadeMapThread

    # Finally, define an executor type (subclass of DocumentMapModuleExecutor) that creates a pool of the right sort
    class ModuleExecutor(MultiprocessingMapModuleExecutor):
        POOL_TYPE = FactoryMadeMapPool

        def preprocess(self):
            super(ModuleExecutor, self).preprocess()
            if preprocess_fn is not None:
                preprocess_fn(self)

        def postprocess(self, error=False):
            super(ModuleExecutor, self).postprocess(error=error)
            if postprocess_fn is not None:
                postprocess_fn(self, error=error)

    return ModuleExecutor


class WorkerStartupError(Exception):
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        super(WorkerStartupError, self).__init__(*args, **kwargs)
