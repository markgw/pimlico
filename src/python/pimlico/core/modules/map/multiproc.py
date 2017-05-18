# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

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
    DocumentMapModuleExecutor, WorkerStartupError, WorkerShutdownError
from pimlico.core.modules.map.threaded import ThreadingMapThread
from pimlico.utils.pipes import qget


class MultiprocessingMapProcess(multiprocessing.Process, DocumentMapProcessMixin):
    """
    A base implementation of document map parallelization using multiprocessing. Note that not all document
    map modules will want to use this: e.g. if you call a background service that provides parallelization
    itself (like the CoreNLP module) there's no need for multiprocessing in the Python code.

    """
    def __init__(self, input_queue, output_queue, exception_queue, executor, docs_per_batch=1):
        multiprocessing.Process.__init__(self)
        DocumentMapProcessMixin.__init__(self, input_queue, output_queue, exception_queue,
                                         docs_per_batch=docs_per_batch)
        self.executor = executor
        self.info = executor.info
        self.daemon = True
        self.stopped = multiprocessing.Event()
        self.initialized = multiprocessing.Event()
        self.no_more_inputs = multiprocessing.Event()

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
                        # Buffer input documents, so that we can process multiple at once if requested
                        input_buffer.append(tuple([archive, filename] + docs))
                    if len(input_buffer) >= self.docs_per_batch or self.no_more_inputs.is_set():
                        results = self.process_documents(input_buffer)
                        for input_tuple, result in zip(input_buffer, results):
                            self.output_queue.put(ProcessOutput(input_tuple[0], input_tuple[1], result))
                        input_buffer = []
            finally:
                try:
                    self.tear_down()
                except Exception, e:
                    self.exception_queue.put(WorkerShutdownError("error in tear_down() call", cause=e), block=True)
        except Exception, e:
            # If there's any uncaught exception, make it available to the main process
            # Include the formatted stack trace, since we can't get this later from the exception outside this process
            e.traceback = format_exc()
            self.exception_queue.put(e, block=True)
        finally:
            # Even there was an error, set initialized so that the main process can wait on it
            self.initialized.set()


class MultiprocessingMapPool(DocumentProcessorPool):
    """
    A base implementation of document map parallelization using multiprocessing.

    """
    PROCESS_TYPE = None
    # Can specify an alternative implementation of the process type when we only need a single process
    SINGLE_PROCESS_TYPE = None

    def __init__(self, executor, processes):
        super(MultiprocessingMapPool, self).__init__(processes)
        self.executor = executor
        self.workers = [self.start_worker() for i in range(processes)]
        # Wait until all of the workers have completed their initialization
        for worker in self.workers:
            worker.initialized.wait()
            # Check whether the worker had an error during initialization
            try:
                e = self.exception_queue.get_nowait()
            except Empty:
                # No error
                pass
            else:
                if hasattr(e, "traceback"):
                    debugging_info = e.traceback
                else:
                    debugging_info = None
                raise WorkerStartupError("error starting up worker process: %s" % e, cause=e,
                                         debugging_info=debugging_info)

    def start_worker(self):
        if self.processes == 1 and self.SINGLE_PROCESS_TYPE is not None:
            return self.SINGLE_PROCESS_TYPE(self.input_queue, self.output_queue, self.exception_queue, self.executor)
        else:
            return self.PROCESS_TYPE(self.input_queue, self.output_queue, self.exception_queue, self.executor)

    @staticmethod
    def create_queue(maxsize=None):
        return multiprocessing.Queue(maxsize)

    def shutdown(self):
        # Tell all the threads to stop
        for worker in self.workers:
            worker.stopped.set()

        # Now wait until all processes have shut down
        still_alive = []
        for worker in self.workers:
            worker.join(5.)
            if worker.is_alive():
                # Extreme case: 5 seconds without the worker closing down
                still_alive.append(worker)
        for worker in still_alive:
            # Output something so we know that it's the worker shutdown that's holding things up
            self.executor.log.warn("Worker process %s taking a long time to shut down: you may need to forcibly kill "
                                   "everything" % worker)
            worker.join()

        # Clear the output queue now, as something might have appeared there since we told the process to shutdown
        while not self.output_queue.empty():
            self.output_queue.get_nowait()

        # Also need to clear the exception queue
        errors = []
        while not self.exception_queue.empty():
            error = self.exception_queue.get_nowait()
            if error is not None:
                errors.append(error)

        if errors:
            # Hopefully, this shouldn't happen, as errors should already have been handled further up
            error = errors[0]
            if hasattr(error, "debugging_info"):
                # We've already attached debugging info at some lower level: just use it
                debugging = error.debugging_info
            elif hasattr(error, "traceback"):
                debugging = error.traceback
            else:
                debugging = None
            if len(errors) > 1:
                extra_mess = " (%d further unhandled errors received from worker processes)" % (len(errors)-1)
            else:
                extra_mess = ""

            self.executor.log.error("error in worker process received while shutting down pool: %s%s" %
                                    (error, extra_mess), cause=error, debugging_info=debugging)

    def notify_no_more_inputs(self):
        for worker in self.workers:
            worker.notify_no_more_inputs()


class MultiprocessingMapModuleExecutor(DocumentMapModuleExecutor):
    POOL_TYPE = None

    def create_pool(self, processes):
        return self.POOL_TYPE(self, processes)

    def postprocess(self, error=False):
        self.pool.shutdown()


def multiprocessing_executor_factory(process_document_fn, preprocess_fn=None, postprocess_fn=None,
                                     worker_set_up_fn=None, worker_tear_down_fn=None, batch_docs=None,
                                     multiprocessing_single_process=False):
    """
    Factory function for creating an executor that uses the multiprocessing-based implementations of document-map
    pools and worker processes.
    This is an easy way to implement a parallelizable executor, which is suitable for a large number of module
    types.

    process_document_fn should be a function that takes the following arguments (unless `batch_docs` is given):

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

    If `batch_docs` is not None, `process_document_fn` is treated differently. Instead of supplying the
    `process_document()` of the worker, it supplies a `process_documents()`. The second argument is a list of tuples,
    each of which is assumed to be the args to `process_document()` for a single document. In this case,
    `docs_per_batch` is set on the worker processes, so that the given number of docs are collected from the input
    and passed into `process_documents()` at once.

    By default, if only a single process is needed, we use the threaded implementation of a map process instead of
    multiprocessing. If this doesn't work out in your case, for some reason, specify
    `multiprocessing_single_process=True` and a mutiprocessing process will be used even when only creating one.

    """
    if isinstance(process_document_fn, type):
        if not issubclass(process_document_fn, MultiprocessingMapProcess):
            raise TypeError("called multiprocessing_executor_factory with a worker type that's not a subclass of "
                            "MultiprocessingMapProcess: got %s" % process_document_fn.__name__)
        worker_type = process_document_fn
    else:
        # Define a worker process type
        class FactoryMadeMapProcess(MultiprocessingMapProcess):
            def __init__(self, input_queue, output_queue, exception_queue, executor):
                super(FactoryMadeMapProcess, self).__init__(input_queue, output_queue, exception_queue, executor,
                                                            docs_per_batch=batch_docs or 1)

            def set_up(self):
                if worker_set_up_fn is not None:
                    worker_set_up_fn(self)

            def tear_down(self):
                if worker_tear_down_fn is not None:
                    worker_tear_down_fn(self)

        if batch_docs is not None:
            FactoryMadeMapProcess.process_documents = process_document_fn
        else:
            FactoryMadeMapProcess.process_document = process_document_fn
        worker_type = FactoryMadeMapProcess

        if multiprocessing_single_process:
            # Don't define a special single-process case
            single_worker_type = None
        else:
            # Also define a different worker thread type for use when we only need a single process
            class FactoryMadeMapSingleProcess(ThreadingMapThread):
                def process_document(self, archive, filename, *docs):
                    return process_document_fn(self, archive, filename, *docs)

                def set_up(self):
                    if worker_set_up_fn is not None:
                        worker_set_up_fn(self)

                def tear_down(self):
                    if worker_tear_down_fn is not None:
                        worker_tear_down_fn(self)

            if batch_docs is not None:
                FactoryMadeMapSingleProcess.process_documents = process_document_fn
            else:
                FactoryMadeMapSingleProcess.process_document = process_document_fn
            single_worker_type = FactoryMadeMapSingleProcess

    # Define a pool type to use this worker process type
    class FactoryMadeMapPool(MultiprocessingMapPool):
        PROCESS_TYPE = worker_type
        SINGLE_PROCESS_TYPE = single_worker_type

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
