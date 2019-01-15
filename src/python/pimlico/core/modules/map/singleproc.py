# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Sometimes the simple multiprocessing-based approach to map module parallelization just isn't suitable.
This module provides an equivalent set of implementations and convenience functions that don't use
multiprocessing, but conform to the pool-based execution pattern by creating a single-thread pool.

"""
from .threaded import ThreadingMapModuleExecutor, ThreadingMapThread, ThreadingMapPool


class SingleThreadMapModuleExecutor(ThreadingMapModuleExecutor):
    def create_pool(self, processes):
        return super(SingleThreadMapModuleExecutor, self).create_pool(1)


def single_process_executor_factory(process_document_fn, preprocess_fn=None, postprocess_fn=None,
                                    worker_set_up_fn=None, worker_tear_down_fn=None, batch_docs=None,
                                    allow_skip_output=False):
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

    If ``allow_skip_output==True`` and the process document function returns None as one of
    its outputs, that document will simply not be written to that output.

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
    class ModuleExecutor(SingleThreadMapModuleExecutor):
        POOL_TYPE = FactoryMadeMapPool
        ALLOW_SKIP_OUTPUT = allow_skip_output

        def preprocess(self):
            super(ModuleExecutor, self).preprocess()
            if preprocess_fn is not None:
                preprocess_fn(self)

        def postprocess(self, error=False):
            super(ModuleExecutor, self).postprocess(error=error)
            if postprocess_fn is not None:
                postprocess_fn(self, error=error)

    return ModuleExecutor
