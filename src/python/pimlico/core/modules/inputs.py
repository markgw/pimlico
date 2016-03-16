"""
Base classes and utilities for input modules in a pipeline.

"""
from .base import BaseModuleInfo
from pimlico.core.modules.base import BaseModuleExecutor


class InputModuleInfo(BaseModuleInfo):
    """
    Base class for input modules. These don't get executed in general, they just provide a way to iterate over
    input data.

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
    class DatatypeInputModuleInfo(InputModuleInfo):
        module_type_name = "%s_input" % datatype.datatype_name
        module_outputs = [("data", datatype)]
        module_options = datatype.input_module_options

        def instantiate_output_datatype(self, output_name, output_datatype):
            return output_datatype.create_from_options(self.get_output_dir(), self.options)

    if datatype.requires_data_preparation:
        # This module needs to be executed
        class DataPreparationExecutor(BaseModuleExecutor):
            def execute(self, module_instance_info):
                # Get the datatype instance
                datatype_instance = module_instance_info.get_output("data")
                # Run the special data preparation method
                datatype_instance.prepare_data(self.log)

        DatatypeInputModuleInfo.module_executable = True
        DatatypeInputModuleInfo.module_executor_override = DataPreparationExecutor

    return DatatypeInputModuleInfo
