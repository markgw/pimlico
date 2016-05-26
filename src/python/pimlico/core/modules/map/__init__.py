import threading
from Queue import Queue, Empty
from threading import Thread
from time import sleep
from traceback import format_exc

from pimlico.core.modules.base import BaseModuleInfo, BaseModuleExecutor
from pimlico.core.modules.execute import ModuleExecutionError, StopProcessing
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.tar import TarredCorpus, AlignedTarredCorpora, TarredCorpusWriter
from pimlico.utils.core import multiwith
from pimlico.utils.progress import get_progress_bar


class DocumentMapModuleInfo(BaseModuleInfo):
    """
    Abstract module type that maps each document in turn in a corpus. It produces a single output
    document for every input.

    Subclasses should specify the input types, which should all be subclasses of
    TarredCorpus, and output types, the first of which (i.e. default) should also be a
    subclass of TarredCorpus. The base class deals with iterating over the input(s) and
    writing the outputs to a new TarredCorpus. The subclass only needs to implement the
    mapping function applied to each document (in its executor).

    """
    # Most subclasses will want to override this to give a more specific datatype for the output
    module_outputs = [("documents", TarredCorpus)]

    def get_writer(self, output_name, output_dir, append=False):
        """
        Get the writer instance that will be given processed documents to write. Should return
        a subclass of TarredCorpusWriter. The default implementation instantiates a plain
        TarredCorpusWriter.

        """
        return TarredCorpusWriter(output_dir, append=append)

    def get_writers(self, append=False):
        # Only include the outputs that are tarred corpus types
        # This allows there to be other outputs aside from those mapped to
        outputs = [name for name in self.output_names if isinstance(self.get_output(name), TarredCorpus)]
        return tuple(self.get_writer(name, self.get_absolute_output_dir(name), append=append) for name in outputs)

    def get_detailed_status(self):
        status_lines = super(DocumentMapModuleInfo, self).get_detailed_status()
        if self.status == "PARTIALLY_PROCESSED":
            status_lines.append("Processed %d documents" % self.get_metadata()["docs_completed"])
            status_lines.append("Last doc completed: %s" % self.get_metadata()["last_doc_completed"])
        return status_lines


class DocumentMapModuleExecutor(BaseModuleExecutor):
    """
    Base class for executors for document map modules. Subclasses should provide the behaviour
    for each individual document by defining a pool (and worker processes) to handle the documents as
    they're fed into it.

    Note that in most cases it won't be necessary to override the pool and worker base classes yourself.
    Unless you need special behaviour, use the standard implementations and factory functions.

    Although the pattern of execution for all document map modules is based on parallel processing (creating a pool,
    spawning worker processes, etc), this doesn't mean that all such modules have to be parallelizable. If you
    have no reason not to parallelize, it's recommended that you do (with single-process execution as a special
    case). However, sometimes parallelizing isn't so simple: in these cases, consider using the tools in
    :mod:.singleproc.

    """
    def __init__(self, module_instance_info, **kwargs):
        super(DocumentMapModuleExecutor, self).__init__(module_instance_info, **kwargs)

        # We may have multiple inputs, which should be aligned tarred corpora
        # If there's only one, this also works
        inputs = [self.info.get_input(input_name) for input_name in self.info.input_names]
        # We also allow (additional) inputs that are not tarred corpora, which get left out of this
        self.input_corpora = [corpus for corpus in inputs if isinstance(corpus, TarredCorpus)]
        if len(self.input_corpora) == 0:
            raise ModuleExecutionError(
                "document map module '%s' got no TarredCorpus instances among its inputs" % self.info.module_name)
        self.input_iterator = AlignedTarredCorpora(self.input_corpora)

    def preprocess(self):
        """
        Allows subclasses to define a set-up procedure to be called before corpus processing begins.
        """
        pass

    def postprocess(self, error=False):
        """
        Allows subclasses to define a finishing procedure to be called after corpus processing if finished.
        """
        pass

    def create_pool(self, processes):
        """
        Should return an instance of the pool to be used for document processing. Should generally be a
        subclass of DocumentProcessorPool.

        Always called after preprocess().

        """
        raise NotImplementedError

    def retrieve_processing_status(self):
        # Check the metadata to see whether we've already partially completed this
        if self.info.status == "PARTIALLY_PROCESSED":
            docs_completed = self.info.get_metadata()["docs_completed"]
            first_archive, __, first_filename = self.info.get_metadata()["last_doc_completed"].partition("/")
            start_after = (first_archive, first_filename)
            self.log.info(
                "Module has been partially executed already; picking up where we left off, after doc %s/%s "
                "(skipping %d docs, %d to process)" %
                (start_after[0], start_after[1], docs_completed, (len(self.input_iterator) - docs_completed))
            )
        else:
            docs_completed = 0
            start_after = None
        return docs_completed, start_after

    def update_processing_status(self, docs_completed, archive_name, filename):
        self.info.set_metadata_values({
            "status": "PARTIALLY_PROCESSED",
            "last_doc_completed": "%s/%s" % (archive_name, filename),
            "docs_completed": docs_completed,
        })

    def execute(self):
        # Call the set-up routine, if one's been defined
        self.log.info("Preparing parallel document map execution with %d processes" % self.processes)
        self.preprocess()

        # Start up a pool
        self.pool = self.create_pool(self.processes)

        complete = False
        result_buffer = {}

        docs_completed_now = 0
        docs_completed_before, start_after = self.retrieve_processing_status()
        total_to_process = len(self.input_iterator) - docs_completed_before

        try:
            # Prepare a corpus writer for the output
            with multiwith(*self.info.get_writers(append=start_after is not None)) as writers:
                if total_to_process < 1:
                    # No input documents, don't go any further
                    # We've come in this far so that the writer gets created and finishing up is done:
                    #  might need to finish writing metadata or suchlike if we failed last time once all docs were done
                    self.log.info("No documents to process")
                else:
                    pbar = get_progress_bar(total_to_process, counter=True,
                                            title="%s map" % self.info.module_type_name.replace("_", " ").capitalize())
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
                        while True:
                            try:
                                # Wait a little bit to see if there's a result available
                                result = self.pool.output_queue.get(timeout=0.2)
                            except Empty:
                                # Timed out: check there's not been an error in one of the processes
                                try:
                                    error = self.pool.exception_queue.get_nowait()
                                except Empty:
                                    # No error: just keep waiting
                                    pass
                                else:
                                    # Got an error from a process: raise it
                                    # First empty the exception queue, in case there were multiple errors
                                    sleep(0.05)
                                    while not self.pool.exception_queue.empty():
                                        self.pool.exception_queue.get(timeout=0.1)
                                    # Sometimes, a traceback from within the process is included
                                    debugging = error.traceback if hasattr(error, "traceback") else None
                                    raise ModuleExecutionError("error in worker process: %s" % error,
                                                               cause=error, debugging_info=debugging)
                            except:
                                raise
                            else:
                                # Got a result from a process
                                break
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
            self.postprocess(error=not complete)

            if not complete and self.info.status == "PARTIALLY_PROCESSED":
                self.log.info("Processed documents recorded: restart processing where you left off by calling run "
                              "again once you've fixed the problem (%d docs processed in this run, %d processed in "
                              "total)" % (docs_completed_now, docs_completed_before+docs_completed_now))


def skip_invalid(fn):
    """
    Decorator to apply to document map executor process_document() methods where you want to skip doing any
    processing if any of the input documents are invalid and just pass through the error information.

    Be careful not to confuse this with the process_document() methods on datatypes. You don't need a decorator
    on them to skip invalid documents, as it's not called on them anyway.

    """
    def _fn(self, archive, filename, *docs):
        invalid = [doc for doc in docs if type(doc) is InvalidDocument]
        if len(invalid):
            # If there's more than one InvalidDocument among the inputs, just return the first one
            return invalid[0]
        else:
            return fn(self, archive, filename, *docs)
    return _fn


def invalid_doc_on_error(fn):
    """
    Decorator to apply to process_document() methods that causes all exceptions to be caught and an InvalidDocument
    to be returned as the result, instead of letting the error propagate up and call a halt to the whole corpus
    processing.

    """
    def _fn(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except StopProcessing:
            # Processing was cancelled, killed or otherwise called to a halt
            # Don't report this as an error processing a doc, but raise it
            raise
        except Exception, e:
            # Error while processing the document: output an invalid document, with some error information
            if isinstance(self, TarredCorpus):
                # Decorator wrapped a process_document() method on a datatype
                # Instead of the module name, output the datatype name and its base dir
                return InvalidDocument("datatype:%s[%s]" % (self.datatype_name, self.base_dir),
                                       "%s\n%s" % (e, format_exc()))
            else:
                return InvalidDocument(self.info.module_name,  "%s\n%s" % (e, format_exc()))
    return _fn


class ProcessOutput(object):
    """
    Wrapper for all result data coming out from a worker.
    """
    def __init__(self, archive, filename, data):
        self.data = data
        self.filename = filename
        self.archive = archive


class InputQueueFeeder(Thread):
    """
    Background thread to read input documents from an iterator and feed them onto an input queue for worker
    processes/threads.

    """
    def __init__(self, input_queue, iterator):
        super(InputQueueFeeder, self).__init__()
        self.daemon = True
        self.iterator = iterator
        self.input_queue = input_queue
        self._docs_processing = Queue()
        self.started = threading.Event()
        self._feeding_complete = threading.Event()
        self.exception_queue = Queue(1)
        self.start()

    def get_next_output_document(self):
        while True:
            if self._feeding_complete.is_set():
                # All docs have now been queued
                # Once there are no more docs on _doc_processing, we're done
                try:
                    return self._docs_processing.get_nowait()
                except Empty:
                    return None
            else:
                # Possible that docs_processing is empty, if we're waiting for the feeder
                # Wait until we know what the next document to come out is to be
                # Don't wait forever: can deadlock if we get here twice between the last queue put and the complete
                #  flag being set. Timeout and check whether feeding is complete if we don't get a result soon
                try:
                    return self._docs_processing.get(timeout=0.1)
                except Empty:
                    pass
                # Check there wasn't an error during feeding
                # Happens, e.g., if the input datatype or filter has an error
                try:
                    error = self.exception_queue.get_nowait()
                except Empty:
                    # No error: just keep waiting
                    pass
                else:
                    # Got an error from feed iterator: raise it
                    # First empty the exception queue, in case there were multiple errors
                    sleep(0.05)
                    while not self.exception_queue.empty():
                        self.exception_queue.get(timeout=0.1)
                    # Sometimes, a traceback from within the process is included
                    debugging = error.traceback if hasattr(error, "traceback") else None
                    raise ModuleExecutionError("error in worker process: %s" % error,
                                               cause=error, debugging_info=debugging)

    def run(self):
        try:
            # Keep feeding inputs onto the queue as long as we've got more
            for archive, filename, docs in self.iterator:
                # If the queue is full, this will block until there's room to put the next one on
                self.input_queue.put((archive, filename, docs))
                # Record that we've sent this one off, so we can write the results out in the right order
                self._docs_processing.put((archive, filename))
                # As soon as something's been fed, the output processor can get going
                self.started.set()
            self._feeding_complete.set()
        except Exception, e:
            # Error in iterating over the input data -- actually quite common, since it could involve filter modules
            # Make it available to the main thread
            e.traceback = format_exc()
            self.exception_queue.put(e, block=True)
        finally:
            # Just in case there aren't any inputs
            self.started.set()

    def check_for_error(self):
        """
        Can be called from the main thread to check whether an error has occurred in this thread and raise a
        suitable exception if so

        """
        try:
            error = self.exception_queue.get_nowait()
        except Empty:
            # No error
            pass
        else:
            # Got an error from thread: raise something including it
            # Sometimes, a traceback from within the process is included
            if hasattr(error, "debugging_info"):
                debugging = error.debugging_info
            elif hasattr(error, "traceback"):
                debugging = error.traceback
            else:
                debugging = None
            raise ModuleExecutionError("error in input iterator: %s" % error, cause=error, debugging_info=debugging)


class DocumentProcessorPool(object):
    """
    Base class for pools that provide an easy implementation of parallelization for document map modules.
    Defines the core interface for pools.

    If you're using multiprocessing, you'll want to use the multiprocessing-specific subclass.

    """
    def __init__(self, processes):
        self.output_queue = self.create_queue()
        self.input_queue = self.create_queue(2*processes)
        self.exception_queue = self.create_queue()
        self.processes = processes

    @staticmethod
    def create_queue(maxsize=None):
        """
        May be overridden by subclasses to provide different implementations of a Queue. By default, uses the
        multiprocessing queue type. Whatever is returned, it should implement the interface of Queue.Queue.

        """
        return Queue(maxsize=maxsize)


class DocumentMapProcessMixin(object):
    """
    Mixin/base class that should be implemented by all worker processes for document map pools.

    """
    def __init__(self, input_queue, output_queue, exception_queue):
        self.exception_queue = exception_queue
        self.output_queue = output_queue
        self.input_queue = input_queue

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
