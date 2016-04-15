"""
Document map modules can in general be fairly easily parallelized.
"""
from Queue import Queue, Empty
from threading import Thread
import threading

import multiprocessing
from traceback import format_exc

from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor
from pimlico.datatypes.base import InvalidDocument
from pimlico.utils.core import multiwith
from pimlico.utils.progress import get_progress_bar


class DocumentProcessorPool(object):
    """
    Base class for pools that provide an easy implementation of parallelization for document map modules.
    """
    def __init__(self, processes):
        self.output_queue = self.create_output_queue()
        self.input_queue = self.create_input_queue(2*processes)
        self.processes = processes

    @staticmethod
    def create_output_queue():
        """
        May be overridden by subclasses to provide different implementations of a Queue. By default, uses the
        multiprocessing queue type. Whatever is returned, it should implement the interface of Queue.Queue.

        """
        return Queue()

    @staticmethod
    def create_input_queue(size):
        """
        Like create_output_queue(), for accepting inputs.

        """
        return Queue(size)


class ProcessOutput(object):
    """
    Wrapper for all result data coming out from a worker.
    """
    def __init__(self, archive, filename, data):
        self.data = data
        self.filename = filename
        self.archive = archive


class InputQueueFeeder(Thread):
    def __init__(self, input_queue, iterator):
        super(InputQueueFeeder, self).__init__()
        self.daemon = True
        self.iterator = iterator
        self.input_queue = input_queue
        self.docs_processing = Queue()
        self.started = threading.Event()
        self.finished = threading.Event()
        self.start()

    def no_more_outputs(self):
        return self.finished.is_set() and self.docs_processing.empty()

    def get_next_output_document(self):
        if self.no_more_outputs():
            # No more outputs ever expected to come out
            return None
        else:
            # Possible that docs_processing is empty, if we're waiting for the feeder
            # Wait until we know what the next document to come out is to be
            return self.docs_processing.get()

    def run(self):
        # Keep feeding inputs onto the queue as long as we've got more
        for archive, filename, docs in self.iterator:
            # If the queue is full, this will block until there's room to put the next one on
            self.input_queue.put((archive, filename, docs))
            # Record that we've sent this one off, so we can write the results out in the right order
            self.docs_processing.put((archive, filename))
            # As soon as something's been fed, the output processor can get going
            self.started.set()
        # Just in case there aren't any inputs
        self.started.set()
        self.finished.set()


class DocumentMapModuleParallelExecutor(DocumentMapModuleExecutor):
    """
    Inherit from this class, instead of DocumentMapModuleExecutor, to provide parallelization.

    """
    def preprocess_parallel(self):
        """ Defaults to calling preprocess() """
        self.preprocess()

    def postprocess_parallel(self, error=False):
        """ Defaults to calling postprocess() """
        self.postprocess(error=error)

    def create_pool(self, processes):
        """
        Should return an instance of the pool to be used for document processing. Should generally be a
        subclass of DocumentProcessorPool.

        Always called after postprocess_parallel().

        """
        raise NotImplementedError

    def execute(self):
        """
        Gets called instead of execute() if the config asks for multiple processes to be used.

        """
        processes = self.info.pipeline.processes
        if processes < 2:
            # Not multiprocessing: just use the single-core version
            super(DocumentMapModuleParallelExecutor, self).execute()
        else:
            # Call the set-up routine, if one's been defined
            self.log.info("Preparing parallel document map execution with %d processes" % processes)
            self.preprocess_parallel()

            # Start up a pool
            self.pool = self.create_pool(processes)

            complete = False
            result_buffer = {}

            docs_completed_now = 0
            docs_completed_before, start_after = self.retrieve_processing_status()

            pbar = get_progress_bar(len(self.input_iterator) - docs_completed_before,
                                    title="%s map" % self.info.module_type_name.replace("_", " ").capitalize())
            try:
                # Prepare a corpus writer for the output
                with multiwith(*self.info.get_writers(append=start_after is not None)) as writers:
                    # Inputs will be taken from this as they're needed
                    input_iter = iter(self.input_iterator.archive_iter(start_after=start_after))
                    # Set a thread going to feed things onto the input queue
                    input_feeder = InputQueueFeeder(self.pool.input_queue, input_iter)

                    # Wait to make sure the input feeder's fed something into the input queue
                    input_feeder.started.wait()
                    # Check what document we're looking for next
                    next_document = input_feeder.get_next_output_document()

                    while next_document is not None:
                        # Wait for a document coming off the output queue
                        result = self.pool.output_queue.get()
                        # We've got some result, but it might not be the one we're looking for
                        # Add it to a buffer, so we can potentially keep it and only output it when its turn comes up
                        result_buffer[(result.archive, result.filename)] = result.data
                        pbar.update(docs_completed_now + len(result_buffer))

                        # Write out as many as we can of the docs that have been sent and whose output is available
                        #  while maintaining the order they were put in in
                        while next_document in result_buffer:
                            archive, filename = next_document
                            next_output = result_buffer.pop((archive, filename))

                            # Next document processed: output the result precisely as in the single-core case
                            if type(next_output) is InvalidDocument:
                                # Just got a single invalid document out: write it out to every output
                                next_output = [next_output] * len(writers)
                            elif type(next_output) is not tuple:
                                # If the processor produces a single result and there's only one output, fine
                                next_output = (next_output,)
                            if len(next_output) != len(writers):
                                raise ModuleExecutionError(
                                    "%s executor's process_document() returned %d results for a document, but the "
                                    "module has %d outputs" % (type(self).__name__, len(next_output), len(writers))
                                )
                            # Write the result to the output corpora
                            for result, writer in zip(next_output, writers):
                                writer.add_document(archive, filename, result)

                            # Update the module's metadata to say that we've completed this document
                            docs_completed_now += 1
                            self.update_processing_status(docs_completed_before+docs_completed_now, archive, filename)

                            # Check what document we're waiting for now
                            next_document = input_feeder.get_next_output_document()

                pbar.finish()
                complete = True
            finally:
                # Call the finishing-off routine, if one's been defined
                if complete:
                    self.log.info("Document mapping complete. Finishing off")
                else:
                    self.log.info("Document mapping failed. Finishing off")
                self.postprocess_parallel(error=not complete)

                if not complete and self.info.status == "PARTIALLY_PROCESSED":
                    self.log.info("Processed documents recorded: restart processing where you left off by calling run "
                                  "again once you've fixed the problem (%d docs processed in this run, %d processed in "
                                  "total)" % (docs_completed_now, docs_completed_before+docs_completed_now))


class MultiprocessingMapProcess(multiprocessing.Process):
    """
    A base implementation of document map parallelization using multiprocessing. Note that not all document
    map modules will want to use this: e.g. if you call a background service that provides parallelization
    itself (like the CoreNLP module) there's no need for multiprocessing in the Python code.

    """
    def __init__(self, input_queue, output_queue, info):
        super(MultiprocessingMapProcess, self).__init__()
        self.info = info
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True
        self.stopped = multiprocessing.Event()

        self.start()

    def set_up(self):
        """
        Called when the process starts, before it starts accepting documents.

        """
        pass

    def process_document(self, archive, filename, *docs):
        raise NotImplementedError

    def tear_down(self):
        """
        Called from within the process after processing is complete, before exiting.

        """
        pass

    def run(self):
        # Start a Java process running in the background via Py4J: we'll send all our jobs to this
        self.set_up()
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


class MultiprocessingMapPool(DocumentProcessorPool):
    """
    A base implementation of document map parallelization using multiprocessing.

    """
    PROCESS_TYPE = None

    def __init__(self, executor, processes):
        super(MultiprocessingMapPool, self).__init__(processes)
        self.executor = executor
        self.workers = [self.start_worker() for i in range(processes)]

    def start_worker(self):
        return self.PROCESS_TYPE(self.input_queue, self.output_queue, self.executor.info)

    @staticmethod
    def create_input_queue(size):
        return multiprocessing.Queue(size)

    @staticmethod
    def create_output_queue():
        return multiprocessing.Queue()

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
