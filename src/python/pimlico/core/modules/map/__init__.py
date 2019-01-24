import threading
import warnings
from Queue import Queue, Empty, Full
from threading import Thread
from time import sleep
from traceback import format_exc

import sys
from pimlico.core.config import PipelineStructureError
from pimlico.core.modules.base import BaseModuleInfo, BaseModuleExecutor, satisfies_typecheck
from pimlico.core.modules.execute import ModuleExecutionError, StopProcessing
from pimlico.datatypes.corpora import is_invalid_doc, invalid_document
from pimlico.datatypes.corpora.data_points import RawDocumentType
from pimlico.datatypes.corpora.grouped import GroupedCorpus, AlignedGroupedCorpora
from pimlico.utils.core import multiwith
from pimlico.utils.pipes import qget
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
    module_outputs = [("documents", GroupedCorpus(RawDocumentType()))]

    def __init__(self, module_name, pipeline, **kwargs):
        super(DocumentMapModuleInfo, self).__init__(module_name, pipeline, **kwargs)

        # Load all the input datatypes now in order to perform typechecking
        input_datatypes = [self.get_input_datatype(input_name) for input_name in self.input_names]
        # We also allow (additional) inputs that are not grouped corpora, which get left out here
        datasets = [dt for dt in input_datatypes if satisfies_typecheck(dt, GroupedCorpus())]
        if len(datasets) == 0:
            raise PipelineStructureError("document map module '%s' got no GroupedCorpus inputs" % self.module_name)

        # Cache the writers once we initialized them
        self._writers = None
        self._named_writers = None

    def _load_input_readers(self):
        # Prepare the list of document map inputs that will be fed into the executor
        # We may have multiple inputs that are grouped corpora, in which case they're aligned
        # If there's only one, this is also fine
        readers = [self.get_input(input_name) for input_name in self.input_names]
        # We also allow (additional) inputs that are not grouped corpora, which get left out of this list
        datasets = [reader for reader in readers if satisfies_typecheck(reader.datatype, GroupedCorpus())]
        return datasets
    input_corpora = property(_load_input_readers)

    def get_writers(self, append=False):
        if self._writers is None:
            self._writers = tuple([writer for (nm, writer) in self.get_named_writers(append=append)])
        return self._writers

    def get_named_writers(self, append=False):
        if self._named_writers is None:
            # Only include the outputs that are tarred corpus types
            # This allows there to be other outputs aside from those mapped to
            outputs = [name for name in self.output_names
                       if satisfies_typecheck(self.get_output_datatype(name)[1], GroupedCorpus(RawDocumentType()))]
            self._named_writers = tuple((name, self.get_output_writer(name, append=append)) for name in outputs)
        return self._named_writers

    def get_detailed_status(self):
        status_lines = super(DocumentMapModuleInfo, self).get_detailed_status()
        if self.status == "PARTIALLY_PROCESSED":
            status_lines.append("Processed %d documents" % self.get_metadata()["docs_completed"])
            status_lines.append("Last doc completed: %s" % self.get_metadata()["last_doc_completed"])
        return status_lines

    def document(self, output_name=None, **kwargs):
        """
        Instantiate a document of the output type for the given output name (or number), or
        the default output.

        Convenience utility to avoid having to look up the output data point type to do this.

        """
        output_data_point_type = dict(self.get_named_writers())[output_name or self.default_output_name].datatype.data_point_type
        return output_data_point_type(**kwargs)


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
    ALLOW_SKIP_OUTPUT = False

    def __init__(self, module_instance_info, **kwargs):
        super(DocumentMapModuleExecutor, self).__init__(module_instance_info, **kwargs)
        self.input_corpora = self.info.input_corpora
        self.input_iterator = AlignedGroupedCorpora(self.input_corpora)

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
        if self.info.status == "FAILED":
            # If we failed last time, we might have stored progress, but should be a bit more cautious
            start_after = None
            docs_completed = self.info.get_metadata().get("docs_completed", 0)
            if docs_completed > 0:
                last_doc_completed = self.info.get_metadata().get("last_doc_completed", None)
                if last_doc_completed is None:
                    # Progress wasn't properly stored: start from beginning
                    docs_completed = 0
                else:
                    first_archive, __, first_filename = last_doc_completed.partition("/")
                    start_after = (first_archive, first_filename)
                    self.log.info(
                        "Module execution failed previously, but progress was stored; "
                        "picking up where we left off, after doc {}/{} "
                        "(skipping {:,} docs, {:,} to process)".format(
                            start_after[0], start_after[1], docs_completed, (len(self.input_iterator) - docs_completed)
                        )
                    )
        elif self.info.status == "PARTIALLY_PROCESSED":
            docs_completed = self.info.get_metadata()["docs_completed"]
            first_archive, __, first_filename = self.info.get_metadata()["last_doc_completed"].partition("/")
            start_after = (first_archive, first_filename)
            self.log.info(
                "Module has been partially executed already; picking up where we left off, after doc {}/{} "
                "(skipping {:,} docs, {:,} to process)".format(
                    start_after[0], start_after[1], docs_completed, (len(self.input_iterator) - docs_completed)
                )
            )
        else:
            docs_completed = 0
            start_after = None
        return docs_completed, start_after

    def update_processing_status(self, docs_completed, archive_name, filename):
        self.info.set_metadata_values({
            "status": "PARTIALLY_PROCESSED",
            "last_doc_completed": u"%s/%s" % (archive_name, filename),
            "docs_completed": docs_completed,
        })

    def execute(self):
        # Call the set-up routine, if one's been defined
        self.log.info("Preparing parallel document map execution with %d processes" % self.processes)
        self.preprocess()

        # Start up a pool
        try:
            self.pool = self.create_pool(self.processes)
        except WorkerStartupError, e:
            raise ModuleExecutionError(e.message, cause=e.cause, debugging_info=e.debugging_info)

        complete = False
        result_buffer = {}

        input_feeder = None
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
                    self.log.info("Starting execution on {:,} docs".format(total_to_process))
                    # Inputs will be taken from this as they're needed
                    input_iter = iter(self.input_iterator.archive_iter(start_after=start_after))
                    # Set a thread going to feed things onto the input queue
                    input_feeder = InputQueueFeeder(self.pool.input_queue, input_iter,
                                                    complete_callback=self.pool.notify_no_more_inputs)

                    # Wait to make sure the input feeder's fed something into the input queue
                    input_feeder.started.wait()
                    # Check what document we're looking for next
                    next_document = input_feeder.get_next_output_document()

                    while next_document is not None:
                        # Wait for a document coming off the output queue
                        while True:
                            try:
                                # Wait a little bit to see if there's a result available
                                result = qget(self.pool.output_queue, timeout=0.2)
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
                                        qget(self.pool.exception_queue, timeout=0.1)
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
                            if is_invalid_doc(next_output):
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
                                # If allowing skipping outputs, we don't try to write the output if None is returned
                                if result is not None or not self.ALLOW_SKIP_OUTPUT:
                                    writer.add_document(archive, filename, result)

                            # Update the module's metadata to say that we've completed this document
                            docs_completed_now += 1
                            self.update_processing_status(docs_completed_before+docs_completed_now, archive, filename)

                            # Check what document we're waiting for now
                            next_document = input_feeder.get_next_output_document()
                    pbar.finish()
            complete = True
        except ModuleExecutionError, e:
            if self.info.status == "PARTIALLY_PROCESSED":
                self.log.info("Processed documents recorded: restart processing where you left off by calling run "
                              "again once you've fixed the problem (%d docs processed in this run, %d processed in "
                              "total)" % (docs_completed_now, docs_completed_before+docs_completed_now))
                # Set the end status so that the top-level routine doesn't replace it with a generic failure status
                e.end_status = self.info.status
            raise
        finally:
            # Call the finishing-off routine, if one's been defined
            if complete:
                self.log.info("Document mapping complete. Finishing off")
            else:
                self.log.info("Document mapping failed. Finishing off")
            self.postprocess(error=not complete)
            if input_feeder is not None:
                input_feeder.shutdown()


def skip_invalid(fn):
    """
    Decorator to apply to document map executor process_document() methods where you want to skip doing any
    processing if any of the input documents are invalid and just pass through the error information.

    Be careful not to confuse this with the process_document() methods on datatypes. You don't need a decorator
    on them to skip invalid documents, as it's not called on them anyway.

    """
    def _fn(self, archive, filename, *docs):
        invalid = [doc for doc in docs if is_invalid_doc(doc)]
        if len(invalid):
            # If there's more than one InvalidDocument among the inputs, just return the first one
            return invalid[0]
        else:
            return fn(self, archive, filename, *docs)
    return _fn


def skip_invalids(fn):
    """
    Decorator to apply to document map executor process_documents() methods where you want to skip doing any
    processing if any of the input documents are invalid and just pass through the error information.

    """
    def _fn(self, input_tuples):
        invalids = [[doc for doc in args[2:] if is_invalid_doc(doc)] for args in input_tuples]
        # Leave out input tuples where there are invalid docs
        input_tuples = [input_tuple for (input_tuple, invalid) in zip(input_tuples, invalids) if len(invalid) == 0]
        # Only call the inner function in those without invalid docs
        results = fn(self, input_tuples) if len(input_tuples) else []
        # Reinsert a single invalid doc in the positions where they were in the input
        for i, invalid in enumerate(invalids):
            if len(invalid) > 0:
                # As with the single-doc version, use the first invalid doc among the inputs
                results.insert(i, invalid[0])
        return results
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
            # This covers the case of wrapping a process_document() function for a map factory,
            # since the first argument is always the worker process
            return invalid_document(self.info.module_name,  "%s\n%s" % (e, format_exc()))
    return _fn


def invalid_docs_on_error(fn):
    """
    Decorator to apply to process_documents() methods that causes all exceptions to be caught and an InvalidDocument
    to be returned as the result for every input document.

    """
    def _fn(self, input_tuples):
        try:
            return fn(self, input_tuples)
        except StopProcessing:
            # Processing was cancelled, killed or otherwise called to a halt
            # Don't report this as an error processing a doc, but raise it
            raise
        except Exception, e:
            # Error while processing the document: output invalid documents, with some error information
            return [invalid_document(self.info.module_name,  "%s\n%s" % (e, format_exc()))] * len(input_tuples)
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
    def __init__(self, input_queue, iterator, complete_callback=None):
        super(InputQueueFeeder, self).__init__()
        self.complete_callback = complete_callback
        self.daemon = True
        self.iterator = iterator
        self.input_queue = input_queue
        self._docs_processing = Queue()
        self.started = threading.Event()
        self.feeding_complete = threading.Event()
        self.cancelled = threading.Event()
        self.ended = threading.Event()
        self.exception_queue = Queue(1)
        # Accumulate a list of invalid docs that have been fed, just for information
        self.invalid_docs = Queue()
        self._invalid_docs_list = []
        self.start()

    def get_next_output_document(self):
        while True:
            if self.feeding_complete.is_set():
                # All docs have now been queued
                # Once there are no more docs on _doc_processing, we're done
                try:
                    return self._docs_processing.get_nowait()
                except Empty:
                    return None
            elif self.cancelled.is_set():
                # Not finished feeding, but cancelled, so don't return a doc
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
                    if hasattr(error, "traceback"):
                        debugging = "Traceback from worker process:\n%s" % error.traceback
                    else:
                        debugging = None
                    raise ModuleExecutionError("error in worker process: %s" % error,
                                               cause=error, debugging_info=debugging)

    def check_invalid(self, archive, filename):
        """
        Checks whether a given document was invalid in the input. Once the check has been performed, the
        item is removed from the list, for efficiency, so this should only be called once per document.
        """
        # Update the invalid docs list from the queue
        while not self.invalid_docs.empty():
            self._invalid_docs_list.append(self.invalid_docs.get_nowait())
        self._invalid_docs_list = [d for d in self._invalid_docs_list if d is not None]
        if (archive, filename) in self._invalid_docs_list:
            self._invalid_docs_list.remove((archive, filename))
            return True
        return False

    def run(self):
        try:
            # Keep feeding inputs onto the queue as long as we've got more
            for i, (archive, filename, docs) in enumerate(self.iterator):
                if self.cancelled.is_set():
                    # Stop feeding right away
                    return
                if any(is_invalid_doc(doc) for doc in docs):
                    self.invalid_docs.put((archive, filename))
                # If the queue is full, this will block until there's room to put the next one on
                # It also blocks if the queue is closed/destroyed/something similar, so we need to check now and
                #  again that we've not been asked to give up
                while True:
                    try:
                        self.input_queue.put((archive, filename, docs), timeout=0.1)
                    except Full:
                        if self.cancelled.is_set():
                            return
                        # Otherwise try putting again
                    else:
                        break
                # Record that we've sent this one off, so we can write the results out in the right order
                self._docs_processing.put((archive, filename))
                # As soon as something's been fed, the output processor can get going
                self.started.set()
            self.feeding_complete.set()
            if self.complete_callback is not None:
                self.complete_callback()
        except Exception, e:
            # Error in iterating over the input data -- actually quite common, since it could involve filter modules
            # Make it available to the main thread
            e.traceback = format_exc()
            self.exception_queue.put(e, block=True)
        finally:
            # Just in case there aren't any inputs
            self.started.set()
            self.ended.set()

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

    def shutdown(self, timeout=3.):
        """
        Cancel the feeder, if it's still feeding and stop the thread. Call only after you're sure
        you no longer need anything from any of the queues. Waits for the thread to end.

        Call from the main thread (that created the feeder) only.

        :type timeout: wait this long for the thread to stop, then give up, outputting a warning. Set to None
            to wait indefinitely

        """
        # Tell the thread to stop feeding, in case it still is
        self.cancelled.set()
        # Wait for the thread to finish executing
        self.ended.wait(timeout=3.)
        if not self.ended.is_set():
            warnings.warn("Input feeding thread didn't close down nicely when asked. You may need to kill "
                          "the application forcibly")
        # Empty all queues, in case there's anything still sitting in any of them
        for q in [self.input_queue, self._docs_processing, self.exception_queue, self.invalid_docs]:
            while True:
                try:
                    q.get_nowait()
                except Empty:
                    break
            if hasattr(q, "task_done"):
                while True:
                    try:
                        q.task_done()
                    except ValueError:
                        # No more undone tasks left
                        break
        # Wait for thread to shut down
        self.join(timeout=timeout)
        # Check whether the join timed out
        if self.is_alive():
            warnings.warn("Input feeding thread took too long to shut down, giving up waiting. You may need to kill "
                          "the application forcibly")
            return False
        return True


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
        self._queues = [self.output_queue, self.input_queue, self.exception_queue]

    def notify_no_more_inputs(self):
        pass

    @staticmethod
    def create_queue(maxsize=None):
        """
        May be overridden by subclasses to provide different implementations of a Queue. By default, uses the
        multiprocessing queue type. Whatever is returned, it should implement the interface of Queue.Queue.

        """
        return Queue(maxsize=maxsize)

    def shutdown(self):
        # Subclasses should override this to shut down all workers
        pass

    def empty_all_queues(self):
        for q in self._queues:
            # Don't rely on q.empty(), which can be wrong in the case of multiprocessing
            while True:
                try:
                    q.get_nowait()
                except Empty:
                    break


class DocumentMapProcessMixin(object):
    """
    Mixin/base class that should be implemented by all worker processes for document map pools.

    """
    def __init__(self, input_queue, output_queue, exception_queue, docs_per_batch=1):
        self.docs_per_batch = docs_per_batch
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

    def process_documents(self, doc_tuples):
        """
        Batched version of process_document(). Default implementation just calls process_document() on each document,
        but if you want to group documents together and process multiple at once, you can override this method
        and make sure the `docs_per_batch` is set > 1.

        Each item in the list of doc tuples should be a tuple of the positional args to process_document() --
        i.e. archive_name, filename, doc_from_corpus1, [doc_from corpus2, ...]

        """
        return [self.process_document(*doc_tuple) for doc_tuple in doc_tuples]

    def tear_down(self):
        """
        Called from within the process after processing is complete, before exiting.

        """
        pass

    def notify_no_more_inputs(self):
        """
        Called when there aren't any more inputs to come.
        """
        pass


class WorkerStartupError(Exception):
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        self.debugging_info = kwargs.pop("debugging_info", None)
        super(WorkerStartupError, self).__init__(*args, **kwargs)


class WorkerShutdownError(Exception):
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        super(WorkerShutdownError, self).__init__(*args, **kwargs)
