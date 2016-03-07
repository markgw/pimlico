"""
This module provides base classes for Pimlico modules.

The procedure for creating a new module is the same whether you're contributing a module to the core set in
the Pimlico codebase or a standalone module in your own codebase, or for a specific pipeline.

A Pimlico module is identified by the full Python-path to the Python package that contains it. This
package should be laid out as follows:
 - The module's metadata is defined by a class in info.py called ModuleInfo, which should inherit from
   BaseModuleInfo or one of its subclasses.
 - The module's functionality is provided by a class in exec.py called ModuleExecutor, which should inherit
   from BaseModuleExecutor.

The exec Python module will not be imported until an instance of the module is to be run. This means that
you can import dependencies and do any necessary initialization at the point where it's executed, without
worrying about incurring the associated costs (and dependencies) every time a pipeline using the module
is loaded.

"""
from importlib import import_module


class BaseModuleInfo(object):
    """
    Abstract base class for all pipeline modules' metadata.

    """
    module_type_name = None
    module_options = {}
    module_inputs = []
    module_outputs = []

    @classmethod
    def process_module_options(cls, opt_dict):
        """
        Parse the options in a dictionary (probably from a config file),
        checking that they're valid for this model type.

        :param opt_dict: dict of options, keyed by option name
        :return: dict of options
        """
        options = {}
        for name, value in opt_dict.items():
            if name not in cls.module_options:
                raise ModuleOptionParseError("invalid option for %s module: '%s'" % name)
            # Postprocess the option value
            opt_config = cls.module_options[name]
            if "type" in opt_config:
                try:
                    value = opt_config["type"](value)
                except Exception, e:
                    raise ModuleOptionParseError("error processing option value '%s' for %s option in %s module: %s" %
                                                 (value, name, cls.module_type_name, e))
                options[name] = value
            else:
                # Just use string value
                options[name] = value

        # Check for unspecified options
        for opt_name, opt_config in cls.module_options.items():
            # Look for options we've not already processed
            if opt_name not in options:
                if "default" in opt_config:
                    # If a default was specified, use it
                    options[opt_name] = opt_config["default"]
                elif "required" in opt_config and opt_config["required"]:
                    # If the option was required, complain
                    raise ModuleOptionParseError("%s option is required for %s module, but was not given" %
                                                 (opt_name, cls.module_type_name))
                else:
                    # Otherwise, include as None, so the options are all in the dict
                    options[opt_name] = None
        return options


class BaseModuleExecutor(object):
    """
    Abstract base class for executors for Pimlico modules. These are classes that actually
    do the work of executing the module on given inputs, writing to given output locations.

    """
    def execute(self, module_instance_info):
        raise NotImplementedError


class ModuleOptionParseError(Exception):
    pass


class ModuleInfoLoadError(Exception):
    pass


class ModuleExecutorLoadError(Exception):
    pass


def load_module_executor(path):
    """
    Utility for loading the executor class for a module from its full path.
    Just a wrapper around an import, with some error checking.

    :param path: path to Python package containing the module
    :return: class
    """
    executor_path = "%s.exec" % path
    try:
        mod = import_module(executor_path)
    except ImportError:
        raise ModuleInfoLoadError("module %s could not be loaded, could not import path %s" % (path, executor_path))
    if not hasattr(mod, "ModuleExecutor"):
        raise ModuleExecutorLoadError("could not load class %s.ModuleExecutor" % executor_path)
    return mod.ModuleExecutor


def load_module_info(path):
    """
    Utility to load the metadata for a Pimlico pipeline module from its package Python path.

    :param path:
    :return:
    """
    info_path = "%s.info" % path
    try:
        mod = import_module(info_path)
    except ImportError:
        raise ModuleInfoLoadError("module %s could not be imported, could not import %s" % (path, info_path))

    if not hasattr(mod, "ModuleInfo"):
        raise ModuleInfoLoadError("could not load class %s.ModuleInfo" % info_path)
    return mod.ModuleInfo
