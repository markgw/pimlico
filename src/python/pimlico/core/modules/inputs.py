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

    def instantiate_output_datatype(self, output_name, output_datatype):
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
                return super(DatatypeInputModuleInfo, self).get_output_dir(output_name,
                                                                           short_term_store=short_term_store)
            else:
                return self.override_base_dir

        def instantiate_output_datatype(self, output_name, output_datatype):
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
