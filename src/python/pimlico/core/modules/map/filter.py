from pimlico.core.config import PipelineStructureError
from pimlico.core.modules.base import load_module_executor, BaseModuleInfo
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.datatypes.base import InvalidDocument
from pimlico.datatypes.tar import TarredCorpus, AlignedTarredCorpora


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
        self._input_iterator = None
        # To make sure we're ready to iterate over the input data and have all the metadata we need, we must
        #  actually create the output writer now
        output_dir = self.wrapped_module_info.get_absolute_output_dir(self.output_name)
        self.writer = self.wrapped_module_info.get_writer(self.output_name, output_dir)

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
        # Load an executor for the module we're wrapping, so we can use some of its functionality
        executor_cls = load_module_executor(self.wrapped_module_info)
        executor = executor_cls(self.wrapped_module_info)

        # Get hold of the outputs from the previous modules to iterate over them
        input_iterator = self.input_iterator

        complete = False
        invalid_inputs = 0
        invalid_outputs = 0
        # Prepare a corpus writer for the output
        with self.writer as writer:
            # Now that we've created the writer, we should be able to initialize a corresponding reader
            # Of course, we can't read any documents from it, but we can use its postprocessing function
            dummy_reader = self.wrapped_module_info.get_output(self.output_name)

            # Call the set-up routine, if one's been defined
            executor.log.info("Preparing document map execution for filter module %s" %
                              self.wrapped_module_info.module_name)
            executor.preprocess()

            try:
                for archive, filename, docs in \
                        input_iterator.archive_iter(subsample=subsample, start_after=start_after):
                    # Useful to know in output
                    if any(type(d) is InvalidDocument for d in docs):
                        invalid_inputs += 1

                    # Run the document processing on this document
                    results = executor.process_document(archive, filename, *docs)

                    if type(results) is InvalidDocument:
                        # Just got a single invalid document
                        result = results
                    elif type(results) is not tuple:
                        # If the processor only produces a single result and there's only one output, that's fine
                        result = results
                    elif len(results) != len(self.wrapped_module_info.output_names):
                        raise ModuleExecutionError(
                            "%s executor's process_document() returned %d results for a document, but the module has "
                            "%d outputs" % (
                                type(self).__name__, len(results), len(self.wrapped_module_info.output_names)
                            )
                        )
                    else:
                        result = results[self.output_num]

                    # Just for the record (useful output)
                    if type(result) is InvalidDocument:
                        invalid_outputs += 1

                    # Here the normal executor would write the outputs to disk
                    # Instead we simply yield the one we're interested in
                    # Use the writer to convert it from what it expects from the processing to raw text
                    data = writer.document_to_raw_data(result)
                    if not self.raw_data:
                        # If not outputting raw data, now use the output datatype to convert it back from raw text
                        # It may seem a waste of time to convert to and from raw text, but sometimes the conversions
                        #  are not symmetrical: e.g. the output writer might produce raw output and not process it
                        #  before writing to disk
                        data = dummy_reader.process_document(data)
                    yield archive, filename, data

                complete = True
            finally:
                # Call the finishing-off routine, if one's been defined
                executor.postprocess(error=not complete)
                executor.log.info("[%s filter] Input contained %d invalid documents, output contained %d" %
                                  (self.wrapped_module_info.module_name, invalid_inputs, invalid_outputs))

    def data_ready(self):
        """
        Ready to supply this data as soon as all the wrapper module's inputs are ready to produce their data.

        """
        return all(self.wrapped_module_info.get_input(input_name).data_ready()
                   for input_name in self.wrapped_module_info.input_names)


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

    return ModuleInfo(
        module_info_instance.module_name,
        module_info_instance.pipeline,
        inputs=module_info_instance.inputs,
        options={},
        optional_outputs=[]
    )
