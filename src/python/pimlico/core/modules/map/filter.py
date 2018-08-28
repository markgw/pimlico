# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
.. todo::

   Continue updating this for the new datatype system. I've got partway,
   but the reader is still far from finished

"""
import warnings
from Queue import Empty
from time import sleep
from traceback import format_exc

from pimlico.core.config import PipelineStructureError
from pimlico.core.modules.base import BaseModuleInfo, satisfies_typecheck
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import InputQueueFeeder, DocumentMapModuleInfo
from pimlico.datatypes import IterableCorpus
from pimlico.datatypes.corpora import is_invalid_doc
from pimlico.datatypes.corpora.grouped import AlignedGroupedCorpora, GroupedCorpus
from pimlico.utils.pipes import qget


class DocumentMapOutputTypeWrapper(object):
    """
    TODO: This was from the old datatypes system

    Remove it once you've replicated the key bits in the reader class below.

    """
    # Tells you the datatype that this simulates, for typechecking
    non_filter_datatype = None
    wrapped_module_info = None
    output_name = None

    def __init__(self, *args, **kwargs):
        raw_data = kwargs.pop("raw_data", False)
        # We should be a subclass of this datatype, so call its constructor
        self.non_filter_datatype.__init__(self, *args, **kwargs)

        self.raw_data = raw_data

        self.output_num = [name for name, type in self.wrapped_module_info.available_outputs].index(self.output_name)
        self.multiple_outputs = len(self.wrapped_module_info.available_outputs) > 1
        self._input_iterator = None

        # Get hold of the outputs from the previous modules to iterate over them
        self.input_corpora = [self.wrapped_module_info.get_input(input_name)
                              for input_name in self.wrapped_module_info.input_names]
        self.input_iterator = AlignedGroupedCorpora(self.input_corpora)

    def __len__(self):
        # Delegate to input datatypes
        return len(self.input_iterator)

    def __iter__(self):
        for __, doc_name, doc in self.archive_iter():
            yield doc_name, doc

    def archive_iter(self, subsample=None, start_after=None):
        """
        Provides an iterator just like TarredCorpus, but instead of iterating over data read from disk,
        gets it on the fly from the input datatype.

        """
        # To make sure we're ready to iterate over the input data and have all the metadata we need, we must
        #  actually create the output writer now
        output_dir = self.wrapped_module_info.get_absolute_output_dir(self.output_name)
        # Get hold of the outputs from the previous modules to iterate over them
        input_iterator = self.input_iterator

        # Load an executor for the module we're wrapping, so we can use some of its functionality
        executor_cls = self.wrapped_module_info.load_executor()
        executor = executor_cls(self.wrapped_module_info)

        # Call the set-up routine, if one's been defined
        executor.log.info(
            "Preparing document map execution for filter module %s" % self.wrapped_module_info.module_name
        )
        executor.preprocess()

        # Start up a processing pool, but only ever use a single process
        executor.pool = executor.create_pool(1)

        complete = False
        invalid_inputs = 0
        invalid_outputs = 0
        input_feeder = None
        try:
            # Prepare a corpus writer for the output
            with self.wrapped_module_info.get_writer(self.output_name, output_dir) as writer:
                # Now that we've created the writer, we should be able to initialize a corresponding reader
                # Of course, we can't read any documents from it, but we can use its postprocessing function
                dummy_reader = self.wrapped_module_info.get_output(self.output_name)

                # Set a thread going to feed things onto the input queue
                input_feeder = InputQueueFeeder(
                    executor.pool.input_queue,
                    input_iterator.archive_iter(subsample=subsample, start_after=start_after),
                    complete_callback=executor.pool.notify_no_more_inputs
                )

                # Wait to make sure the input feeder's fed something into the input queue
                input_feeder.started.wait()
                # Check what document we're looking for next
                next_document = input_feeder.get_next_output_document()

                while next_document is not None:
                    # Wait for a document coming off the output queue
                    while True:
                        try:
                            # Wait a little bit to see if there's a result available
                            result = qget(executor.pool.output_queue, timeout=0.2)
                        except Empty:
                            # Timed out: check there's not been an error in one of the processes
                            try:
                                error = executor.pool.exception_queue.get_nowait()
                            except Empty:
                                # No error: just keep waiting
                                pass
                            else:
                                # Got an error from a process: raise it
                                # First empty the exception queue, in case there were multiple errors
                                sleep(0.05)
                                while not executor.pool.exception_queue.empty():
                                    qget(executor.pool.exception_queue, timeout=0.1)
                                # Sometimes, a traceback from within the process is included
                                if hasattr(error, "debugging_info"):
                                    # We've already attached debugging info at some lower level: just use it
                                    debugging = error.debugging_info
                                elif hasattr(error, "traceback"):
                                    debugging = error.traceback
                                else:
                                    debugging = None
                                raise ModuleExecutionError("error in worker process: %s" % error,
                                                           cause=error, debugging_info=debugging)
                            input_feeder.check_for_error()
                        except:
                            raise
                        else:
                            # Got a result from the process
                            break
                    # We've got a result and, since we're only using 1 process, it must be the right one: check
                    if (result.archive, result.filename) != next_document:
                        raise ModuleExecutionError(
                            "something went wrong with filter execution. Expected result for %s/%s, but got %s/%s"
                            % (result.archive, result.filename, next_document[0], next_document[1])
                        )

                    # Next document processed: yield the result
                    if is_invalid_doc(result) or \
                            (self.multiple_outputs and is_invalid_doc(result.data[self.output_num])) or \
                            (not self.multiple_outputs and is_invalid_doc(result.data)):
                        invalid_outputs += 1
                        # Check whether the document was also invalid in the input
                        if input_feeder.check_invalid(result.archive, result.filename):
                            invalid_inputs += 1
                        # Just got a single invalid document out
                        yield result.archive, result.filename, result.data
                    else:
                        # Here the normal executor would write the outputs to disk
                        # Instead we simply yield the one we're interested in
                        # Use the writer to convert it from what it expects from the processing to raw text
                        if self.multiple_outputs:
                            data = result.data[self.output_num]
                        else:
                            data = result.data
                        # If we're outputting raw data, use the writer to convert the data structure to raw data
                        if self.raw_data:
                            data = writer.document_to_raw_data(data)
                        # Historical note:
                        #  Previously, we did a little process here where we converted the doc to raw data and then
                        #  back into the data structure required. This was to allow for writers that aren't symmetrical:
                        #  they expect datatype A, convert it to raw data and write it, but the corresponding reader
                        #  reads the raw data into datatype B. This is a stupid thing to do most of the time. It's
                        #  also stupid to slow down the execution of almost every pipeline to allow for this niche
                        #  case, so I've stopped doing it
                        yield result.archive, result.filename, data
                    # Check what document we're waiting for now
                    next_document = input_feeder.get_next_output_document()

                # We get a None next_document if there's an error in the input feeder at the beginning
                # Check whether this has happened
                input_feeder.check_for_error()

                complete = True
        except Exception, e:
            # Any other uncaught exception should be passed up as a ModuleExecutionError, since we're actually
            #  executing a module here, even though we're pretending to iterate over data
            # This causes the restart procedure to catch the error just as if something went wrong in map execution
            if hasattr(e, "debugging_info"):
                # We've already attached debugging info at some lower level: just use it
                debugging = e.debugging_info
            elif hasattr(e, "traceback"):
                debugging = e.traceback
            else:
                # Just include the stack trace from this process
                debugging = format_exc()

            raise ModuleExecutionError("error in filter %s: %s" % (self.wrapped_module_info.module_name, e),
                                       cause=e, debugging_info=debugging)
        finally:
            # Call the finishing-off routine, if one's been defined
            executor.postprocess(error=not complete)
            executor.log.info("[%s filter] Input contained %d invalid documents, output contained %d" %
                              (self.wrapped_module_info.module_name, invalid_inputs, invalid_outputs))
            if input_feeder is not None:
                input_feeder.check_for_error()
                input_feeder.shutdown()
            # Also shut down the executor's worker pool
            executor.pool.shutdown()

    def data_ready(self):
        """
        Ready to supply this data as soon as all the wrapper module's inputs are ready to produce their data.

        """
        return all(input_type.data_ready()
                   for input_name in self.wrapped_module_info.input_names
                   for input_type in self.wrapped_module_info.get_input(input_name, always_list=True))




class FilterModuleOutputReader(GroupedCorpus.Reader):
    """
    A custom reader that is used for the output of a filter module, producing
    documents on the fly.

    """
    metadata = {}

    def __init__(self, datatype, setup, pipeline, **kwargs):
        # Don't call GroupedCorpus init, but jump up to IterableCorpus
        IterableCorpus.Reader.__init__(self, datatype, setup, pipeline, **kwargs)
        # TODO Set archives and archive_filenames to conform to GroupedCorpus.Reader interface

    def __len__(self):
        # TODO
        pass

    def extract_file(self, archive_name, filename):
        raise NotImplementedError("cannot extract file from filter module reader")

    def list_archive_iter(self):
        for archive, doc_name, doc in self.archive_iter():
            yield archive, doc_name

    def archive_iter(self, start_after=None, skip=None, name_filter=None):
        # TODO This is the big 'un
        # See above for the old one to model on
        pass

    class Setup:
        def __init__(self, datatype, wrapped_module_info, output_name):
            self.wrapped_module_info = wrapped_module_info
            self.output_name = output_name
            self.datatype = datatype

        def ready_to_read(self):
            # Calling missing_data() checks that all input data is available and any other module requirements
            missing_data = self.wrapped_module_info.missing_data()
            return len(missing_data) == 0

    def process_setup(self):
        # Override to not do data path processing
        return



def wrap_module_info_as_filter(module_info_instance):
    """
    Create a filter module from a document map module so that it gets executed on the fly to provide its
    outputs as input to later modules. Can be applied to any document map module simply by adding `filter=T`
    to its config.

    This function is called when `filter=T` is given.

    .. todo::

       Under the new datatype system, this should be done differently.
       Don't wrap datatypes, but instead use the actual output datatypes (taken from
       the wrapped module type's output) and instead create custom readers
       that gets instantiated when fetching the module's output readers.

       I've created the test pipeline filter_tokenize for testing this.

    :param module_info_instance: basic module info to wrap the outputs of
    :return: a new non-executable ModuleInfo whose outputs are produced on the fly and will be identical to
        the outputs of the wrapper module.

    """
    warnings.warn("Filter module wrapper is still being updated for the new datatypes system and "
                  "probably doesn't work yet")
    # Check that this is a document map module: otherwise it doesn't make sense to wrap it
    if not isinstance(module_info_instance, DocumentMapModuleInfo):
        raise PipelineStructureError("cannot create a filter from a %s module, as it's not a document map module "
                                     "(tried to run module '%s' as a filter)" %
                                     (module_info_instance.module_type_name, module_info_instance.module_name))

    # Wrap each of the output datatypes so that it executes the document processing on the fly
    #wrapped_outputs = []
    #for output_name in module_info_instance.output_names:
    #    wrapped_outputs.append((output_name, _wrap_output(module_info_instance, output_name)))

    # Check that all outputs are grouped corpora
    # If not, we can't wrap the module to produce those outputs on the fly
    #   We might want to move this check to within instantiate_output_reader_setup() so that
    #   we can wrap a module with non-grouped corpora outputs if those outputs are never needed.
    #   But then we probably get the error at an odd time
    output_datatypes = [
        (output_name, module_info_instance.get_output_datatype(output_name))
        for output_name in module_info_instance.output_names
    ]
    for (output_name, output_datatype) in output_datatypes:
        if not satisfies_typecheck(output_datatype, GroupedCorpus()):
            raise PipelineStructureError("problem treating module '{}' as a filter. Output '{}' is not a grouped "
                                         "corpus".format(module_info_instance.module_name, output_name))

    class ModuleInfo(BaseModuleInfo):
        module_type_name = "%s_filter" % module_info_instance.module_type_name
        module_options = []
        module_inputs = module_info_instance.module_inputs
        module_outputs = module_info_instance.module_outputs
        module_optional_outputs = []
        module_executable = False

        def instantiate_output_reader_setup(self, output_name, datatype):
            return FilterModuleOutputReader.Setup(datatype, module_info_instance, output_name)

    info = ModuleInfo(
        module_info_instance.module_name,
        module_info_instance.pipeline,
        inputs=module_info_instance.inputs,
        options={},
        optional_outputs=[]
    )
    # Pass through module variables
    info.module_variables = module_info_instance.module_variables
    return info
