# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Base classes and utilities for input modules in a pipeline.

"""
import copy
from pimlico.core.config import PipelineStructureError

from pimlico.datatypes.base import IterableCorpus
from .base import BaseModuleInfo
from pimlico.core.modules.base import BaseModuleExecutor


class InputModuleInfo(BaseModuleInfo):
    """
    Base class for input modules. These don't get executed in general, they just provide a way to iterate over
    input data.

    You probably don't want to subclass this. It's usually simplest to define a datatype for reading the input
    data and then just specify its class as the module's type. This results in a subclass of this module info
    being created dynamically to read that data.

    Note that module_executable is typically set to False and the base class does this. However, some input
    modules need to be executed before the input is usable, for example to collect stats about the input
    data.

    """
    module_type_name = "input"
    module_executable = False

    def instantiate_output_datatype(self, output_name, output_datatype, **kwargs):
        raise NotImplementedError("input module type (%s) must implement its own datatype instantiator" %
                                  self.module_type_name)


def input_module_factory(datatype):
    """
    Create an input module class to load a given datatype.

    """
    input_module_options = copy.copy(datatype.input_module_options)
    if issubclass(datatype, IterableCorpus):
        # Also get input options from the document type
        input_module_options.update(datatype.data_point_type.input_module_options)

    # Add a special option to allow a dir to be specified to read the data from
    # This will become the base_dir for the datatype when instantiated
    input_module_options["dir"] = {
        "help": "Directory to read the data from. May be used to load a dataset from an output from another "
                "Pimlico pipeline. If not given, the datatype's base dir will be the expected base dir within "
                "this pipeline's data directory, which usually won't exist",
    }

    class DatatypeInputModuleInfo(InputModuleInfo):
        module_type_name = "%s_input" % datatype.datatype_name
        module_readable_name = "%s datatype input" % datatype.datatype_name
        module_outputs = [("data", datatype)]
        module_options = input_module_options

        def __init__(self, module_name, pipeline, **kwargs):
            super(DatatypeInputModuleInfo, self).__init__(module_name, pipeline, **kwargs)
            self.override_base_dir = self.options["dir"]

        def get_output_dir(self, output_name, short_term_store=False):
            if self.override_base_dir is None:
                if datatype.requires_data_preparation:
                    # During data preparation, this directly will be created and some data stored there
                    # The data is only ready once we pass data_ready() in the normal way
                    return super(DatatypeInputModuleInfo, self).get_output_dir(output_name,
                                                                               short_term_store=short_term_store)
                else:
                    # No data preparation required, which means that this input datatype never stores anything
                    # It therefore has a None base_dir, which causes the datatype to be satisfied without it,
                    # providing any further checks provided by its data_ready() are satisfied
                    return None
            else:
                return self.override_base_dir

        def instantiate_output_datatype(self, output_name, output_datatype, **kwargs):
            return output_datatype.create_from_options(self.get_output_dir(output_name), self.pipeline,
                                                       copy.deepcopy(self.options), module=self)

    if datatype.requires_data_preparation:
        # This module needs to be executed
        class DataPreparationExecutor(BaseModuleExecutor):
            def execute(self):
                # Get the datatype instance
                datatype_instance = self.info.get_output("data")
                # Run the special data preparation method
                datatype_instance.prepare_data(self.info.get_absolute_output_dir("data"), self.log)

        DatatypeInputModuleInfo.module_executable = True
        DatatypeInputModuleInfo.module_executor_override = DataPreparationExecutor

    return DatatypeInputModuleInfo


def iterable_corpus_reader_datatype_factory(data_point_type, len_function, iterator_function, data_ready_function):
    """
    Creates a datatype for reading in input according to input module options and allowing it to
    be iterated over by other modules.

    Typically used together with `iterable_input_reader_factory()`.

    ``len_function`` should be a function that takes the processed input module options and returns
    the length of the corpus (number of documents).

    ``iterator_function`` should take the processed input module options and return an iterator over the
    corpus' documents (e.g. a generator function). Each item yielded should be a pair ``(doc_name, data)``
    and ``data`` should be in the appropriate internal format associated with the document type.

    ``data_ready_function`` should take the processed input module options and return True if the data
    is ready to be read in.

    """
    dp_type = data_point_type

    class OutputType(IterableCorpus):
        datatype_name = "reader_iterator"
        data_point_type = dp_type

        def __init__(self, reader_options, pipeline, **kwargs):
            super(OutputType, self).__init__(None, pipeline, **kwargs)
            self.reader_options = reader_options

        def __len__(self):
            return len_function(self.reader_options)

        def __iter__(self):
            return iterator_function(self.reader_options)

        def data_ready(self):
            return data_ready_function(self.reader_options)


def iterable_input_reader_factory(input_module_options, output_type, module_type_name=None):
    """
    Factory for creating an input reader module type. This is a non-executable module that has no
    inputs. It reads its data from some external location, using the given module options. The resulting
    dataset is an IterableCorpus subtype, with the given document type.

    ``output_type`` is a datatype that performs the actual iteration over the data and is instantiated
    with the processed options as its first argument. This is typically created using
    `iterable_corpus_reader_datatype_factory()`.

    **How is this different from ``input_module_factory``?** This method is used in your module code
    to prepare a ModuleInfo class for reading a particular type of input data and presenting it as a
    Pimlico dataset of the given type. ``input_module_factory``, on the other hand, is used by Pimlico
    when you specify a datatype as a module type in a config file.

    Note that, in future versions, reading datasets output by another Pimlico pipeline will be the only
    purpose for that special notation. The possibility of specifying ``input_module_options`` to create
    an input reader will disappear, so the use of ``input_module_options`` should be phased out and replaced
    with input reader modules, such as those created by this factory.

    """
    dp_type = output_type.data_point_type
    mt_name = module_type_name or "reader_for_{}".format(dp_type.__name__)

    class IterableInputReaderModuleInfo(InputModuleInfo):
        module_type_name = mt_name
        module_readable_name = "Input reader for {} iterable corpus".format(dp_type.__name__)
        module_outputs = [("corpus", output_type)]
        module_options = input_module_options

        def instantiate_output_datatype(self, output_name, output_datatype, **kwargs):
            return output_type(self.options, self.pipeline)

    return IterableInputReaderModuleInfo
