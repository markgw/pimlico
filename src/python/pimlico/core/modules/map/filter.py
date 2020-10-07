# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Filter-mode execution

Any document map module can be executed in filter mode.
Instead of performing processing on each document and writing the
output to a corpus, this mode performs the document-level processing
on the fly and yields the results in order, providing a new
iterable (grouped) corpus for the next module, without storing anything.

"""
from builtins import object

from traceback import format_exc

from pimlico.core.config import PipelineStructureError
from pimlico.core.modules.base import BaseModuleInfo, satisfies_typecheck
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import DocumentMapModuleInfo, DocumentMapper
from pimlico.datatypes import IterableCorpus, DatatypeLoadError
from pimlico.datatypes.corpora import is_invalid_doc
from pimlico.datatypes.corpora.grouped import AlignedGroupedCorpora, GroupedCorpus


class FilterModuleOutputReader(GroupedCorpus.Reader):
    """
    A custom reader that is used for the output of a filter module, producing
    documents on the fly.

    """
    metadata = {}

    def __init__(self, datatype, setup, pipeline, **kwargs):
        # Don't call GroupedCorpus init, but jump up to IterableCorpus
        IterableCorpus.Reader.__init__(self, datatype, setup, pipeline, **kwargs)
        # Prepare the reader for all the inputs
        self.input_corpora = setup.wrapped_module_info.input_corpora
        # Construct the align corpus reader
        self.input_iterator = AlignedGroupedCorpora(self.input_corpora)
        # Set archives and archive_filenames to conform to GroupedCorpus.Reader interface
        # These are taken directly from the first input corpus and is assumed to be unchanged
        self.archives = self.input_corpora[0].archives
        self.archive_filenames = self.input_corpora[0].archive_filenames

    def __len__(self):
        return len(self.input_iterator)

    def extract_file(self, archive_name, filename):
        raise NotImplementedError("cannot extract file from filter module reader")

    def list_archive_iter(self):
        for archive, doc_name, doc in self.archive_iter():
            yield archive, doc_name

    def archive_iter(self, start_after=None, skip=None, name_filter=None):
        # Get hold of the outputs from the previous modules to iterate over them
        output_num = self.setup.output_num

        # Load an executor for the module we're wrapping, so we can use some of its functionality
        executor_cls = self.setup.wrapped_module_info.load_executor()
        executor = executor_cls(self.setup.wrapped_module_info)

        # Call the set-up routine, if one's been defined
        executor.log.info(
            "Preparing document map execution for filter module %s" % self.setup.wrapped_module_info.module_name
        )
        invalid_inputs = 0
        invalid_outputs = 0

        try:
            # Inputs will be taken from this as they're needed
            input_iter = iter(
                self.input_iterator.archive_iter(start_after=start_after, skip=skip, name_filter=name_filter)
            )

            # Set map processing going, using the generic function
            mapper = DocumentMapper(executor, input_iter, record_invalid=True)
            # Only ever use a single process for a filter module
            for (archive, doc_name), next_output in mapper.map_documents():
                # Accumulate counts of invalid documents
                if any(is_invalid_doc(d) for d in next_output):
                    invalid_outputs += 1
                if mapper.input_feeder.check_invalid(archive, doc_name):
                    invalid_inputs += 1

                # We only take one of the outputs, if there are multiple, and yield this
                yield archive, doc_name, next_output[output_num]
        except Exception as e:
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

            raise ModuleExecutionError("error in filter {}: {}".format(self.setup.wrapped_module_info.module_name, e),
                                       cause=e, debugging_info=debugging)
        finally:
            executor.log.info("Filter input contained {:,} invalid documents, output contained {:,}".format(
                invalid_inputs, invalid_outputs
            ))

    class Setup(object):
        def __init__(self, datatype, wrapped_module_info, output_name):
            self.wrapped_module_info = wrapped_module_info
            self.output_name = output_name
            self.datatype = datatype
            # Work out which index the named output is, among the outputs that will
            # be provided by each document's processing call
            output_names = self.wrapped_module_info.get_grouped_corpus_output_names()
            try:
                self.output_num = output_names.index(self.output_name)
            except KeyError:
                raise DatatypeLoadError("output name '{}' not found among document map module's grouped corpus "
                                        "outputs: {}".format(self.output_name, ", ".join(output_names)))

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

    :param module_info_instance: basic module info to wrap the outputs of
    :return: a new non-executable ModuleInfo whose outputs are produced on the fly and will be identical to
        the outputs of the wrapper module.

    """
    # Check that this is a document map module: otherwise it doesn't make sense to wrap it
    if not isinstance(module_info_instance, DocumentMapModuleInfo):
        raise PipelineStructureError("cannot create a filter from a %s module, as it's not a document map module "
                                     "(tried to run module '%s' as a filter)" %
                                     (module_info_instance.module_type_name, module_info_instance.module_name))

    # Check that all outputs are grouped corpora
    # If not, we can't wrap the module to produce those outputs on the fly
    #   We might want to move this check to within instantiate_output_reader_setup() so that
    #   we can wrap a module with non-grouped corpora outputs if those outputs are never needed.
    #   But then we probably get the error at an odd time
    output_datatypes = [
        (output_name, module_info_instance.get_output_datatype(output_name))[1]
        for output_name in module_info_instance.output_names
    ]
    for (output_name, output_datatype) in output_datatypes:
        if not satisfies_typecheck(output_datatype, GroupedCorpus()):
            raise PipelineStructureError("problem treating module '{}' as a filter. Output '{}' is not a grouped "
                                         "corpus, but {}".format(module_info_instance.module_name, output_name, output_datatype))

    class ModuleInfo(BaseModuleInfo):
        module_type_name = "%s_filter" % module_info_instance.module_type_name
        module_options = []
        module_inputs = module_info_instance.module_inputs
        module_outputs = module_info_instance.module_outputs
        module_optional_outputs = []
        module_executable = False
        module_supports_python2 = module_info_instance.module_supports_python2

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
