"""
Document map modules can in general be fairly easily parallelized.
"""
from multiprocessing import Queue

from itertools import islice

from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleExecutor
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.tar import AlignedTarredCorpora
from pimlico.utils.core import multiwith
from pimlico.utils.progress import get_progress_bar


class DocumentProcessorPool(object):
    """
    Base class for pools that provide an easy implementation of parallelization for document map modules.
    """
    def __init__(self, processes):
        self.queue = self.create_queue()
        self.processes = processes

    @staticmethod
    def create_queue():
        """
        May be overridden by subclasses to provide different implementations of a Queue. By default, uses the
        multiprocessing queue type. Whatever is returned, it should implement the interface of Queue.Queue.

        """
        return Queue()

    def process_document(self, archive, filename, *docs):
        """
        Lightweight method to be called from the main process to fire off the processing in a worker
        process. The worker should place its output, wrapped in a ProcessOutput, on the output_queue when
        finished. This method should return without blocking.
        """
        raise NotImplementedError


class ProcessOutput(object):
    """
    Wrapper for all result data coming out from a worker.
    """
    def __init__(self, archive, filename, data):
        self.data = data
        self.filename = filename
        self.archive = archive


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
            self.log.info("Preparing parallel document map execution for %d documents with %d processes" %
                          (len(self.input_iterator), processes))
            self.preprocess_parallel()

            # Start up a pool
            self.pool = self.create_pool(processes)
            output_queue = self.pool.queue
            self.log.info("Process pool created for processing %d documents in parallel" % processes)

            complete = False
            docs_processing = []
            result_buffer = {}

            docs_completed_now = 0
            docs_completed_before, start_after = self.retrieve_processing_status()

            self.log.info("Processing %d documents" % (len(self.input_iterator) - docs_completed_before))
            pbar = get_progress_bar(len(self.input_iterator) - docs_completed_before,
                                    title="%s map" % self.info.module_type_name.replace("_", " ").capitalize())
            try:
                # Prepare a corpus writer for the output
                with multiwith(*self.info.get_writers(append=start_after is not None)) as writers:
                    # Inputs will be taken from this as they're needed
                    input_iter = iter(self.input_iterator.archive_iter(start_after=start_after))
                    # Push the first inputs into the pool
                    # Send the pool enough to occupy every process and keep one in reserve for each
                    for archive, filename, docs in islice(input_iter, processes*2):
                        self.pool.process_document(archive, filename, *docs)
                        # Keep track of the order we need the results in
                        docs_processing.append((archive, filename))

                    # Look for the first document coming off the queue
                    while len(docs_processing):
                        result = output_queue.get()
                        # We've got some result, but it might not be the one we're looking for
                        # Add it to a buffer, so we can potentially keep it and only output it when its turn comes up
                        result_buffer[(result.archive, result.filename)] = result.data
                        # Before doing anything else, set the next job going
                        try:
                            archive, filename, docs = input_iter.next()
                        except StopIteration:
                            # No more documents to send: just receive the remaining results until we've got all the
                            # ones we've already sent
                            pass
                        else:
                            self.pool.process_document(archive, filename, *docs)
                            docs_processing.append((archive, filename))

                        # Write out as many as we can of the docs that have been sent and whose output is available
                        #  while maintaining the order they were put in in
                        while len(docs_processing) and docs_processing[0] in result_buffer:
                            archive, filename = docs_processing.pop(0)
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
                            pbar.update(docs_completed_now)
                            self.update_processing_status(docs_completed_before+docs_completed_now, archive, filename)

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
                                  "again once you've fixed the problem")
