# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Just like multiprocessing, but using threading instead. If you're not sure which you should use, it's probably
multiprocessing.

"""
from __future__ import absolute_import

import threading
from Queue import Empty, Queue
from traceback import format_exc

from pimlico.core.modules.map import ProcessOutput, DocumentProcessorPool, DocumentMapProcessMixin, \
    DocumentMapModuleExecutor, WorkerStartupError
from pimlico.datatypes.base import InvalidDocument
from pimlico.utils.pipes import qget


class ThreadingMapThread(threading.Thread, DocumentMapProcessMixin):
    def __init__(self, input_queue, output_queue, exception_queue, executor):
        threading.Thread.__init__(self)
        DocumentMapProcessMixin.__init__(self, input_queue, output_queue, exception_queue)
        self.executor = executor
        self.info = executor.info
        self.daemon = True
        self.stopped = threading.Event()
        self.initialized = threading.Event()
        self.no_more_inputs = threading.Event()

        self.start()

    def notify_no_more_inputs(self):
        self.no_more_inputs.set()

    def run(self):
        try:
            # Run any startup routine that the subclass has defined
            self.set_up()
            # Notify waiting processes that we've finished initialization
            self.initialized.set()
            input_buffer = []
            try:
                while not self.stopped.is_set():
                    try:
                        # Timeout and go round the loop again to check whether we're supposed to have stopped
                        archive, filename, docs = qget(self.input_queue, timeout=0.05)
                    except Empty:
                        # Don't worry if the queue is empty: just keep waiting for more until we're shut down
                        pass
                    else:
                        input_buffer.append(tuple([archive, filename] + docs))
                        if len(input_buffer) >= self.docs_per_batch or self.no_more_inputs.is_set():
                            results = self.process_documents(input_buffer)
                            for input_tuple, result in zip(input_buffer, results):
                                self.output_queue.put(ProcessOutput(input_tuple[0], input_tuple[1], result))
                            input_buffer = []
            finally:
                self.tear_down()
        except Exception, e:
            # If there's any uncaught exception, make it available to the main process
            self.exception_queue.put_nowait(e)
        finally:
            # Even there was an error, set initialized so that the main process can wait on it
            self.initialized.set()


class ThreadingMapPool(DocumentProcessorPool):
    THREAD_TYPE = None

    def __init__(self, executor, processes):
        super(ThreadingMapPool, self).__init__(processes)
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
                raise WorkerStartupError("error in worker process: %s" % e, cause=e)

    def start_worker(self):
        return self.THREAD_TYPE(self.input_queue, self.output_queue, self.exception_queue, self.executor)

    @staticmethod
    def create_queue(maxsize=None):
        return Queue(maxsize)

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


class ThreadingMapModuleExecutor(DocumentMapModuleExecutor):
    POOL_TYPE = None

    def create_pool(self, processes):
        return self.POOL_TYPE(self, processes)

    def postprocess(self, error=False):
        self.pool.shutdown()


def threading_executor_factory(process_document_fn, preprocess_fn=None, postprocess_fn=None,
                               worker_set_up_fn=None, worker_tear_down_fn=None):
    """
    Factory function for creating an executor that uses the threading-based implementations of document-map
    pools and worker processes.

    process_document_fn should be a function that takes the following arguments:

    - the worker process instance (allowing access to things set during setup)
    - archive name
    - document name
    - the rest of the args are the document itself, from each of the input corpora

    If proprocess_fn is given, it is called from the main thread once before execution begins, with the executor
    as an argument.

    If postprocess_fn is given, it is called from the main thread at the end of execution, including on the way
    out after an error, with the executor as an argument and a kwarg *error* which is True if execution failed.

    If worker_set_up_fn is given, it is called within each worker before execution begins, with the worker thread
    instance as an argument.
    Likewise, worker_tear_down_fn is called from within the worker thread before it exits.

    Alternatively, you can supply a worker type, a subclass of :class:.ThreadingMapThread, as the first argument.
    If you do this, worker_set_up_fn and worker_tear_down_fn will be ignored.

    """
    if isinstance(process_document_fn, type):
        if not issubclass(process_document_fn, ThreadingMapThread):
            raise TypeError("called threading_executor_factory with a worker type that's not a subclass of "
                            "ThreadingMapThread: got %s" % process_document_fn.__name__)
        worker_type = process_document_fn
    else:
        # Define a worker thread type
        class FactoryMadeMapThread(ThreadingMapThread):
            def process_document(self, archive, filename, *docs):
                return process_document_fn(self, archive, filename, *docs)

            def set_up(self):
                if worker_set_up_fn is not None:
                    worker_set_up_fn(self)

            def tear_down(self):
                if worker_tear_down_fn is not None:
                    worker_tear_down_fn(self)
        worker_type = FactoryMadeMapThread

    # Define a pool type to use this worker process type
    class FactoryMadeMapPool(ThreadingMapPool):
        THREAD_TYPE = worker_type

    # Finally, define an executor type (subclass of DocumentMapModuleExecutor) that creates a pool of the right sort
    class ModuleExecutor(ThreadingMapModuleExecutor):
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
