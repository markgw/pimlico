# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from Queue import Empty
from time import sleep
from traceback import print_exc, format_exc

from pimlico.core.config import PipelineStructureError
from pimlico.core.modules.base import load_module_executor, BaseModuleInfo
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import InputQueueFeeder, DocumentMapModuleInfo
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.tar import TarredCorpus, AlignedTarredCorpora
from pimlico.utils.pipes import qget


class DocumentMapOutputTypeWrapper(object):
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
        self.input_iterator = AlignedTarredCorpora(self.input_corpora)

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
                    if type(result) is InvalidDocument or \
                            (self.multiple_outputs and type(result.data[self.output_num]) is InvalidDocument) or \
                            (not self.multiple_outputs and type(result.data) is InvalidDocument):
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
                input_feeder.cancel()
                input_feeder.empty_all_queues()

    def data_ready(self):
        """
        Ready to supply this data as soon as all the wrapper module's inputs are ready to produce their data.

        """
        return all(input_type.data_ready()
                   for input_name in self.wrapped_module_info.input_names
                   for input_type in self.wrapped_module_info.get_input(input_name, always_list=True))


def _wrap_output(module_info_instance, inner_output_name):
    __, output_datatype = module_info_instance.get_output_datatype(inner_output_name)

    if not issubclass(output_datatype, TarredCorpus):
        # Can only wrap TarredCorpus outputs of a document map
        raise PipelineStructureError("problem treating module '%s' as a filter. Tried to wrap output '%s' with a "
                                     "datatype that produces the output on the fly, but it's not a subclass of "
                                     "TarredCorpus" % (module_info_instance.module_name, inner_output_name))

    # Create a special subclass of the general output wrapper for this output
    # Doing so using type() instead of a class def allows us to give it an informative class name
    wrapper_cls = type(
        "%sFilterWrapper" % output_datatype.__name__,
        (DocumentMapOutputTypeWrapper, output_datatype),
        dict(
            non_filter_datatype=output_datatype,
            wrapped_module_info=module_info_instance,
            output_name=inner_output_name,
        )
    )

    return wrapper_cls


def wrap_module_info_as_filter(module_info_instance):
    """
    Create a filter module from a document map module so that it gets executed on the fly to provide its
    outputs as input to later modules. Can be applied to any document map module simply by adding `filter=T`
    to its config.

    This function is called when `filter=T` is given.

    :param module_info_instance: basic module info to wrap the outputs of
    :return: a new non-executable ModuleInfo whose outputs are produced on the fly and will be identical to
        the outputs of the wrapper module.

    """
    # Check that this is a document map module: otherwise it doesn't make sense to wrap it
    if not isinstance(module_info_instance, DocumentMapModuleInfo):
        raise PipelineStructureError("cannot create a filter from a %s module, as it's not a document map module "
                                     "(tried to run module '%s' as a filter)" %
                                     (module_info_instance.module_type_name, module_info_instance.module_name))

    # Wrap each of the output datatypes so that it executes the document processing on the fly
    wrapped_outputs = []
    for output_name in module_info_instance.output_names:
        wrapped_outputs.append((output_name, _wrap_output(module_info_instance, output_name)))

    class ModuleInfo(BaseModuleInfo):
        module_type_name = "%s_filter" % module_info_instance.module_type_name
        module_options = []
        module_inputs = module_info_instance.module_inputs
        module_outputs = wrapped_outputs
        module_optional_outputs = []
        module_executable = False

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
