"""
Base classes and utilities for input modules in a pipeline.

"""
from .base import BaseModuleExecutor, ModuleTypeError, BaseModuleInfo


class InputModuleInfo(BaseModuleInfo):
    """
    Base class for input modules. These don't get executed, they just provide a way to iterate over
    input data.

    """
    def instantiate_output_datatype(self, output_name, output_datatype):
        raise NotImplementedError("input module type (%s) must implement its own datatype instantiator" %
                                  self.module_type_name)


class InputModuleExecutor(BaseModuleExecutor):
    def execute(self, module_instance_info):
        raise ModuleTypeError("cannot execute an input module: execute the modules it feeds into to use it")
