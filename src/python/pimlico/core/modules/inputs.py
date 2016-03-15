"""
Base classes and utilities for input modules in a pipeline.

"""
from .base import BaseModuleInfo


class InputModuleInfo(BaseModuleInfo):
    """
    Base class for input modules. These don't get executed in general, they just provide a way to iterate over
    input data.

    Note that module_executable is typically set to False and the base class does this. However, some input
    modules need to be executed before the input is usable, for example to collect stats about the input
    data.

    """
    def instantiate_output_datatype(self, output_name, output_datatype):
        raise NotImplementedError("input module type (%s) must implement its own datatype instantiator" %
                                  self.module_type_name)
