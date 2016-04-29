"""
Document map modules can in general be easily parallelized using multiprocessing. This module provides
implementations of a pool and base worker processes that use multiprocessing, making it dead easy to
implement a parallelized module, simply by defining what should be done on each document.

In particular, use :fun:.multiprocessing_executor_factory wherever possible.

"""
from __future__ import absolute_import

import multiprocessing
from Queue import Empty
from traceback import format_exc

from pimlico.core.modules.map import ProcessOutput, DocumentProcessorPool, DocumentMapProcessMixin, \
    DocumentMapModuleExecutor
from pimlico.datatypes.base import InvalidDocument


class MultiprocessingMapProcess(multiprocessing.Process, DocumentMapProcessMixin):
    """
    A base implementation of document map parallelization using multiprocessing. Note that not all document
    map modules will want to use this: e.g. if you call a background service that provides parallelization
    itself (like the CoreNLP module) there's no need for multiprocessing in the Python code.

    """
    def __init__(self, input_queue, output_queue, exception_queue, executor):
        multiprocessing.Process.__init__(self)
        DocumentMapProcessMixin.__init__(self, input_queue, output_queue, exception_queue)
        self.executor = executor
        self.info = executor.info
        self.daemon = True
        self.stopped = multiprocessing.Event()
        self.initialized = multiprocessing.Event()

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
            self.exception_queue.put_nowait(e)
        finally:
            # Even there was an error, set initialized so that the main process can wait on it
            self.initialized.set()


class MultiprocessingMapPool(DocumentProcessorPool):
    """
    A base implementation of document map parallelization using multiprocessing.

    """
    PROCESS_TYPE = None

    def __init__(self, executor, processes):
        super(MultiprocessingMapPool, self).__init__(processes)
        self.executor = executor
        self.workers = [self.start_worker() for i in range(processes)]
        # Wait until all of the workers have completed their initialization
        for worker in self.workers:
            worker.initialized.wait()
            # Check whether the worker had an error during initialization
            try:
                e = worker.exception_queue.get_nowait()
            except Empty:
                # No error
                pass
            else:
                raise ProcessStartupError("error in worker process: %s" % e, cause=e)

    def start_worker(self):
        return self.PROCESS_TYPE(self.input_queue, self.output_queue, self.exception_queue, self.executor)

    @staticmethod
    def create_queue(maxsize=None):
        return multiprocessing.Queue(maxsize)

    def shutdown(self):
        # Tell all the threads to stop
        for worker in self.workers:
            worker.stopped.set()
        for worker in self.workers:
            # Wait until it's stopped
            while worker.is_alive():
                # Need to clear the output queue, or else the join hangs
                while not self.output_queue.empty():
                    self.output_queue.get_nowait()
                worker.join(0.1)


class MultiprocessingMapModuleExecutor(DocumentMapModuleExecutor):
    POOL_TYPE = None

    def create_pool(self, processes):
        return self.POOL_TYPE(self, processes)

    def postprocess(self, error=False):
        self.pool.shutdown()


def multiprocessing_executor_factory(process_document_fn, preprocess_fn=None, postprocess_fn=None,
                                     worker_set_up_fn=None, worker_tear_down_fn=None):
    """
    Factory function for creating an executor that uses the multiprocessing-based implementations of document-map
    pools and worker processes.
    This is an easy way to implement a parallelizable executor, which is suitable for a large number of module
    types.

    process_document_fn should be a function that takes the following arguments:

    - the worker process instance (allowing access to things set during setup)
    - archive name
    - document name
    - the rest of the args are the document itself, from each of the input corpora

    If proprocess_fn is given, it is called from the main process once before execution begins, with the executor
    as an argument.

    If postprocess_fn is given, it is called from the main process at the end of execution, including on the way
    out after an error, with the executor as an argument and a kwarg *error* which is True if execution failed.

    If worker_set_up_fn is given, it is called within each worker before execution begins, with the worker process
    instance as an argument.
    Likewise, worker_tear_down_fn is called from within the worker process before it exits.

    Alternatively, you can supply a worker type, a subclass of :class:.MultiprocessingMapProcess, as the first argument.
    If you do this, worker_set_up_fn and worker_tear_down_fn will be ignored.

    """
    if isinstance(process_document_fn, type):
        if not issubclass(process_document_fn, MultiprocessingMapProcess):
            raise TypeError("called multiprocessing_executor_factory with a worker type that's not a subclass of "
                            "MultiprocessingMapProcess: got %s" % process_document_fn.__name__)
        worker_type = process_document_fn
    else:
        # Define a worker process type
        class FactoryMadeMapProcess(MultiprocessingMapProcess):
            def process_document(self, archive, filename, *docs):
                return process_document_fn(self, archive, filename, *docs)

            def set_up(self):
                if worker_set_up_fn is not None:
                    worker_set_up_fn(self)

            def tear_down(self):
                if worker_tear_down_fn is not None:
                    worker_tear_down_fn(self)
        worker_type = FactoryMadeMapProcess

    # Define a pool type to use this worker process type
    class FactoryMadeMapPool(MultiprocessingMapPool):
        PROCESS_TYPE = worker_type

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


class ProcessStartupError(Exception):
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        super(ProcessStartupError, self).__init__(*args, **kwargs)
