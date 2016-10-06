# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
This module provides base classes for Pimlico modules.

The procedure for creating a new module is the same whether you're contributing a module to the core set in
the Pimlico codebase or a standalone module in your own codebase, or for a specific pipeline.

A Pimlico module is identified by the full Python-path to the Python package that contains it. This
package should be laid out as follows:

- The module's metadata is defined by a class in info.py called ModuleInfo, which should inherit from
  BaseModuleInfo or one of its subclasses.
- The module's functionality is provided by a class in execute.py called ModuleExecutor, which should inherit
  from BaseModuleExecutor.

The exec Python module will not be imported until an instance of the module is to be run. This means that
you can import dependencies and do any necessary initialization at the point where it's executed, without
worrying about incurring the associated costs (and dependencies) every time a pipeline using the module
is loaded.

"""
import json
import shutil
from datetime import datetime
from importlib import import_module
from operator import itemgetter

import os
import warnings
from pimlico.core.config import PipelineStructureError
from pimlico.core.modules.options import process_module_options
from pimlico.datatypes.base import PimlicoDatatype, DynamicOutputDatatype, DynamicInputDatatypeRequirement, \
    MultipleInputs
from pimlico.utils.core import remove_duplicates


class BaseModuleInfo(object):
    """
    Abstract base class for all pipeline modules' metadata.

    """
    module_type_name = None
    module_readable_name = None
    module_options = {}
    module_inputs = []
    """ Specifies a list of (name, datatype class) pairs for outputs that are always written """
    module_outputs = []
    """
    Specifies a list of (name, datatype class) pairs for outputs that are written only if they're specified
    in the "output" option or used by another module
    """
    module_optional_outputs = []
    """
    Whether the module should be executed
    Typically True for almost all modules, except input modules (though some of them may also require execution) and
    filters
    """
    module_executable = True
    """ If specified, this ModuleExecutor class will be used instead of looking one up in the exec Python module """
    module_executor_override = None
    """
    Usually None. In the case of stages of a multi-stage module, stores a pointer to the main module.

    """
    main_module = None

    def __init__(self, module_name, pipeline, inputs={}, options={}, optional_outputs=[], docstring=""):
        self.docstring = docstring
        self.inputs = inputs
        self.options = options
        self.module_name = module_name
        self.pipeline = pipeline

        self.default_output_name = (self.module_outputs+self.module_optional_outputs)[0][0]

        # Work out what outputs this module will make available
        if len(self.module_outputs + self.module_optional_outputs) == 0:
            # Need at least one output
            if len(self.module_optional_outputs):
                raise PipelineStructureError(
                    "module %s has no outputs. Select at least one optional output from [%s] using the 'output' option"
                    % (self.module_name, ", ".join(name for name, dt in self.module_optional_outputs))
                )
            else:
                raise PipelineStructureError("module %s defines no outputs" % self.module_name)
        # The basic outputs are always available
        self.available_outputs = list(self.module_outputs)
        # Others may be requested in the config, given to us in optional_outputs
        # Also include those that are used as inputs to other modules
        used_output_names = self.pipeline.used_outputs.get(self.module_name, [])
        # Replace None with the default output name (which could be an optional output if no non-optional are defined)
        used_output_names = set([name if name is not None else self.default_output_name for name in used_output_names])
        # Include all of these outputs in the final output list
        self.available_outputs.extend((name, dt) for (name, dt) in self.module_optional_outputs
                                      if name in set(optional_outputs)|used_output_names)

        self._metadata = None
        self._history = None

    def __repr__(self):
        return "%s(%s)" % (self.module_type_name, self.module_name)

    def load_executor(self):
        """
        Loads a ModuleExecutor for this Pimlico module. Usually, this just involves calling
        :func:`load_module_executor`, but the default executor loading may be overridden for a particular module
        type by overriding this function. It should always return a subclass of ModuleExecutor, unless there's
        an error.

        """
        return load_module_executor(self)

    @classmethod
    def get_key_info_table(cls):
        """
        When generating module docs, the table at the top of the page is produced by calling this method. It should
        return a list of two-item lists (title + value). Make sure to include the super-class call if you override
        this to add in extra module-specific info.

        """
        return []

    @property
    def metadata_filename(self):
        return os.path.join(self.pipeline.find_data_path(self.get_module_output_dir(), default="short"), "metadata")

    def get_metadata(self):
        if self._metadata is None:
            # Try loading metadata
            self._metadata = {}
            if os.path.exists(self.metadata_filename):
                with open(self.metadata_filename, "r") as f:
                    data = f.read()
                    if data.strip("\n "):
                        try:
                            self._metadata = json.loads(data)
                        except ValueError:
                            # Couldn't parse as JSON
                            # Include the old attribute-value format for backwards compatibility
                            # TODO Remove this later
                            self._metadata = dict(itemgetter(0, 2)(line.partition(": ")) for line in data.splitlines())
        return self._metadata

    def set_metadata_value(self, attr, val):
        self.set_metadata_values({attr: val})

    def set_metadata_values(self, val_dict):
        # Make sure we've got an output directory to output the metadata to
        # Always write to short-term store, don't search others
        if not os.path.exists(self.get_module_output_dir(short_term_store=True)):
            os.makedirs(self.get_module_output_dir(short_term_store=True))
        # Load the existing metadata
        metadata = self.get_metadata()
        # Add our new values to it
        metadata.update(val_dict)
        # Write the whole thing out to the file
        with open(os.path.join(self.get_module_output_dir(short_term_store=True), "metadata"), "w") as f:
            json.dump(metadata, f, indent=4)

    def __get_status(self):
        # Check the metadata for current module status
        return self.get_metadata().get("status", "UNEXECUTED")

    def __set_status(self, status):
        self.set_metadata_value("status", status)

    status = property(__get_status, __set_status)

    @property
    def execution_history_path(self):
        return os.path.join(self.pipeline.find_data_path(self.get_module_output_dir(), default="short"), "history")

    def add_execution_history_record(self, line):
        """
        Output a single line to the file that stores the history of module execution, so we can trace what we've done.

        """
        # Prepare a timestamp for the message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.execution_history_path, "a") as history:
            history.write("{timestamp} {message}\n".format(timestamp=timestamp, message=line))
        # Invalidate the cache
        self._history = None

    @property
    def execution_history(self):
        """
        Get the entire recorded execution history for this module. Returns an empty string if no history has
        been recorded.

        """
        if self._history is None:
            # Read history in from a file if one's available
            if os.path.exists(self.execution_history_path):
                with open(self.execution_history_path, "r") as history:
                    self._history = history.read()
            else:
                self._history = ""
        return self._history

    @property
    def input_names(self):
        return [name for name, __ in self.module_inputs]

    @property
    def output_names(self):
        return [name for name, __ in self.available_outputs]

    @classmethod
    def process_module_options(cls, opt_dict):
        """
        Parse the options in a dictionary (probably from a config file),
        checking that they're valid for this model type.

        :param opt_dict: dict of options, keyed by option name
        :return: dict of options
        """
        module_options = dict(cls.module_options)
        return process_module_options(module_options, opt_dict, cls.module_type_name)

    @classmethod
    def extract_input_options(cls, opt_dict, module_name=None, previous_module_name=None):
        """
        Given the config options for a module instance, pull out the ones that specify where the
        inputs come from and match them up with the appropriate input names.

        The inputs returned are just names as they come from the config file. They are split into
        module name and output name, but they are not in any way matched up with the modules they
        connect to or type checked.

        :param module_name: name of the module being processed, for error output. If not given, the name
            isn't included in the error.
        :param previous_module_name: name of the previous module in the order given in the config file, allowing
            a single-input module to default to connecting to this if the input connection wasn't given
        :return: dictionary of inputs
        """
        inputs = {}
        for opt_name, opt_value in opt_dict.items():
            if opt_name == "input":
                # Allow the name "input" to be used where there's only one input
                if len(cls.module_inputs) == 1:
                    inputs[cls.module_inputs[0][0]] = opt_dict.pop("input")
                else:
                    raise ModuleInfoLoadError(
                        "plain 'input' option was given to %s module%s, but %s modules have %d inputs. Use "
                        "'input_<input_name>' instead" % (cls.module_type_name,
                                                          (" %s" % module_name) if module_name else "",
                                                          cls.module_type_name, len(cls.module_inputs)))
            elif opt_name.startswith("input_"):
                input_name = opt_name[6:]
                if input_name not in dict(cls.module_inputs):
                    raise ModuleInfoLoadError("%s module%s got unknown input '%s'. Available inputs: %s" % (
                        cls.module_type_name, (" %s" % module_name) if module_name else "",
                        input_name, ", ".join([i[0] for i in cls.module_inputs])
                    ))
                inputs[input_name] = opt_dict.pop(opt_name)

        # Allow a special case of a single-input module whose input is unspecified and defaults to the
        # default output from the previous module in the order given in the config file
        if len(inputs) == 0 and len(cls.module_inputs) == 1 and previous_module_name is not None:
            inputs[cls.module_inputs[0][0]] = previous_module_name

        # Check for any inputs that weren't specified
        unspecified_inputs = set(i[0] for i in cls.module_inputs) - set(inputs.keys())
        if unspecified_inputs:
            raise ModuleInfoLoadError("%s module%s has unspecified input%s '%s'" % (
                cls.module_type_name, (" %s" % module_name) if module_name else "",
                "s" if len(unspecified_inputs) > 1 else "", ", ".join(unspecified_inputs)
            ))

        # Split up the input specifiers
        for input_name, input_spec in inputs.items():
            # Multiple inputs may be specified, separated by commas
            # This will only work if the input datatype is a MultipleInputs
            inputs[input_name] = []
            for spec in input_spec.split(","):
                # Split off any additional datatype specifiers: there could be multiple (recursive)
                spec_parts = spec.split("->")
                spec = spec_parts[0]
                additional_names = spec_parts[1:]  # Most of the time this is empty

                if "." in spec:
                    # This is a module name + output name
                    module_name, __, output_name = spec.rpartition(".")
                else:
                    # Just a module name, using the default output
                    module_name = spec
                    output_name = None
                inputs[input_name].append((module_name, output_name, additional_names))

        return inputs

    @staticmethod
    def get_extra_outputs_from_options(options):
        """
        Normally, which optional outputs get produced by a module depend on the 'output' option given in the
        config file, plus any outputs that get used by subsequent modules. By overriding this method, module
        types can add extra outputs into the list of those to be included, conditional on other options.

        E.g. the corenlp module include the 'annotations' output if annotators are specified, so that the
        user doesn't need to give both options.

        """
        return []

    @classmethod
    def process_config(cls, config_dict, module_name=None, previous_module_name=None):
        """
        Convenience wrapper to do all config processing from a dictionary of module config.

        """
        options = dict(config_dict)
        # Remove the "type" option if it's still in there
        options.pop("type", None)
        # Pull out the output option if it's there, to specify optional outputs
        output_opt = options.pop("output", "")
        outputs = output_opt.split(",") if output_opt else []
        # Pull out the input options and match them up with inputs
        inputs = cls.extract_input_options(options, module_name=module_name, previous_module_name=previous_module_name)
        # Process the rest of the values as module options
        options = cls.process_module_options(options)

        # Get additional outputs to be included on the basis of the options, according to module type's own logic
        outputs = set(outputs) | set(cls.get_extra_outputs_from_options(options))

        return inputs, outputs, options

    def get_module_output_dir(self, short_term_store=False):
        """
        Gets the path to the base output dir to be used by this module, relative to the storage base dir.
        When outputting data, the storage base dir will always be the short term store path, but when looking
        for the output data other base paths might be explored, including the long term store.

        :param short_term_store: if True, return absolute path to output dir in short-term store (used for output)
        :return: path, relative to store base path, or if short_term_store=True absolute path to output dir
        """
        relative_dir = self.module_name
        if short_term_store:
            return os.path.join(self.pipeline.short_term_store, relative_dir)
        else:
            return relative_dir

    def get_absolute_output_dir(self, output_name):
        return os.path.join(self.get_module_output_dir(short_term_store=True), output_name)

    def get_output_dir(self, output_name, short_term_store=False):
        return os.path.join(self.get_module_output_dir(short_term_store=short_term_store), output_name)

    def get_output_datatype(self, output_name=None, additional_names=[]):
        if output_name is None:
            # Get the default output
            # Often there'll be only one output, so a name needn't be specified
            # If there are multiple, the first is the default
            output_name = self.default_output_name

        outputs = dict(self.available_outputs)
        if output_name not in outputs:
            raise PipelineStructureError("%s module does not have an output named '%s'. Available outputs: %s" %
                                         (self.module_type_name, output_name, ", ".join(self.output_names)))
        datatype = outputs[output_name]

        # The datatype might be a dynamic type -- with a function that we call to get the type
        if isinstance(datatype, DynamicOutputDatatype):
            # Call the get_datatype() method to build the actual datatype
            datatype = datatype.get_datatype(self)

        # Recursively retrieve additional datatypes from this one
        additional_names = additional_names or []
        for additional_name in additional_names:
            if additional_name not in dict(datatype.supplied_additional):
                raise PipelineStructureError("datatype '%s' does not supplied an additional datatype by the name of "
                                             "'%s'. Additional datatypes it supplies: %s" %
                                             (datatype.datatype_name, additional_name,
                                              dict(datatype.supplied_additional).keys()))
            datatype = dict(datatype.supplied_additional)[additional_name]

        return output_name, datatype

    def instantiate_output_datatype(self, output_name, output_datatype):
        """
        Subclasses may want to override this to provide special behaviour for instantiating
        particular outputs' datatypes.

        """
        return output_datatype(self.get_output_dir(output_name), self.pipeline)

    def get_output(self, output_name=None, additional_names=None):
        """
        Get a datatype instance corresponding to one of the outputs of the module.

        """
        output_name, datatype = self.get_output_datatype(output_name=output_name)
        output_datatype_instance = self.instantiate_output_datatype(output_name, datatype)
        if additional_names:
            # Use the main output datatype to fetch additional datatype(s)
            for i in range(len(additional_names)):
                additional_name = "->".join(additional_names[:i+1])
                output_datatype_instance = \
                    output_datatype_instance.instantiate_additional_datatype(additional_names[i], additional_name)
        return output_datatype_instance

    def is_multiple_input(self, input_name=None):
        """
        Returns True if the named input (or default input if no name is given) is a MultipleInputs input, False
        otherwise. If it is, get_input() will return a list, otherwise it will return a single datatype.

        """
        if input_name is None:
            input_type = self.module_inputs[0][1]
        else:
            input_type = dict(self.module_inputs)[input_name]
        return isinstance(input_type, MultipleInputs)

    def get_input_module_connection(self, input_name=None, always_list=False):
        """
        Get the ModuleInfo instance and output name for the output that connects up with a named input (or the
        first input) on this module instance. Used by get_input() -- most of the time you probably want to
        use that to get the instantiated datatype for an input.

        If the input type was specified with MultipleInputs, meaning that we're expecting an unbounded number
        of inputs, this is a list. Otherwise, it's a single (module, output_name) pair.
        If always_list=True, in this latter case we return a single-item list.

        """
        if input_name is None:
            if len(self.module_inputs) == 0:
                raise PipelineStructureError("module '%s' doesn't have any inputs. Tried to get the first input" %
                                             self.module_name)
            input_name = self.module_inputs[0][0]
        if input_name not in self.inputs:
            raise PipelineStructureError("module '%s' doesn't have an input '%s'" % (self.module_name, input_name))

        # Try getting hold of the module that we need the output of
        if always_list or self.is_multiple_input(input_name):
            return [(self.pipeline[previous_module_name], output_name, additional_names)
                    for (previous_module_name, output_name, additional_names) in self.inputs[input_name]]
        else:
            previous_module_name, output_name, additional_names = self.inputs[input_name][0]
            return self.pipeline[previous_module_name], output_name, additional_names

    def get_input_datatype(self, input_name=None, always_list=False):
        """
        Get a list of datatype classes corresponding to one of the inputs to the module.
        If an input name is not given, the first input is returned.

        If the input type was specified with MultipleInputs, meaning that we're expecting an unbounded number
        of inputs, this is a list. Otherwise, it's a single datatype.

        """
        datatypes = [
            previous_module.get_output_datatype(output_name, additional_names=additional_names)[1]
            for previous_module, output_name, additional_names in
            self.get_input_module_connection(input_name, always_list=True)
        ]
        return datatypes if always_list or self.is_multiple_input(input_name) else datatypes[0]

    def get_input(self, input_name=None, always_list=False):
        """
        Get a datatype instances corresponding to one of the inputs to the module.
        Looks up the corresponding output from another module and uses that module's metadata to
        get that output's instance.
        If an input name is not given, the first input is returned.

        If the input type was specified with MultipleInputs, meaning that we're expecting an unbounded number
        of inputs, this is a list. Otherwise, it's a single datatype instance.
        If always_list=True, in this latter case we return a single-item list.

        """
        inputs = [
            previous_module.get_output(output_name, additional_names=additional_names)
            for previous_module, output_name, additional_names in
            self.get_input_module_connection(input_name, always_list=True)
        ]
        return inputs if always_list or self.is_multiple_input(input_name) else inputs[0]

    def input_ready(self, input_name=None):
        """
        Check whether the datatype is (or datatypes are) ready to go, corresponding to the named input.

        :param input_name: input to check
        :return: True if input is ready
        """
        return len(self.missing_data([input_name])) == 0

    def all_inputs_ready(self):
        """
        Check `input_ready()` on all inputs.

        :return: True if all input datatypes are ready to be used
        """
        return len(self.missing_data()) == 0

    @classmethod
    def is_filter(cls):
        return not cls.module_executable and len(cls.module_inputs) > 0

    def missing_data(self, input_names=None):
        """
        Check whether all the input data for this module is available. If not, return a list strings indicating
        which outputs of which modules are not available. If it's all ready, returns an empty list.

        To check specific inputs, give a list of input names. To check all inputs, don't specify `input_names`.
        To check the default input, give `input_names=[None]`.

        """
        if input_names is None:
            # Default to checking all inputs
            input_names = self.input_names
        missing = []
        if self.is_input():
            # Don't check inputs for an input module: there aren't any
            # However, the output datatypes might require certain files before the data preparation routine can be run
            for output_name in self.output_names:
                for path in self.get_output(output_name).get_required_paths():
                    if not os.path.exists(path):
                        missing.append("%s (required for '%s' output '%s'" % (path, self.module_name, output_name))
        else:
            for input_name in input_names:
                for previous_module, output_name, additional_names in \
                        self.get_input_module_connection(input_name, always_list=True):
                    # Don't check whether additional datatypes are ready -- supposedly guaranteed if the main is
                    if not previous_module.get_output(output_name).data_ready():
                        # If the previous module is a filter, it's more helpful to say exactly what data it's missing
                        if previous_module.is_filter():
                            missing.extend(previous_module.missing_data())
                        else:
                            missing.append("%s output '%s'" % (previous_module.module_name, output_name))
        return missing

    @classmethod
    def is_input(cls):
        from pimlico.core.modules.inputs import InputModuleInfo
        return issubclass(cls, InputModuleInfo)

    @property
    def dependencies(self):
        """
        :return: list of names of modules that this one depends on for its inputs.
        """
        return remove_duplicates(
            [module_name for input_connections in self.inputs.values()
             for (module_name, output_name, additional_names) in input_connections])

    def typecheck_inputs(self):
        if self.is_input() or len(self.module_inputs) == 0:
            # Nothing to check
            return

        module_inputs = dict(self.module_inputs)
        for input_name, input_connections in self.inputs.items():
            # Check the type of each input in turn
            input_type_requirements = module_inputs[input_name]

            if isinstance(input_type_requirements, MultipleInputs):
                # Type requirements are the same for all inputs
                input_type_requirements = input_type_requirements.datatype_requirements
            elif len(input_connections) > 1:
                # Doesn't accept multiple datatypes on a single input, so shouldn't have more than one
                raise PipelineStructureError("input %s on module '%s' does not accept multiple inputs, but %d were "
                                             "given" % (input_name, self.module_name, len(input_connections)))

            for (dep_module_name, output, additional_names) in input_connections:
                # Load the dependent module
                dep_module = self.pipeline[dep_module_name]
                output_name = output or "default"
                # Try to load the named output (or the default, if no name was given)
                dep_module_output_name, dep_module_output = \
                    dep_module.get_output_datatype(output_name=output, additional_names=additional_names)

                # Check the output datatype is given in a suitable form
                if not (isinstance(dep_module_output, type) and issubclass(dep_module_output, PimlicoDatatype)) and \
                        not isinstance(dep_module_output, DynamicOutputDatatype):
                    raise PipelineStructureError("invalid output datatype from module '%s'. Must be a PimlicoDatatype "
                                                 "subclass or a DynamicOutputDatatype subclass instance: "
                                                 "got %s" % (self.module_name, dep_module_output.__name__))
                try:
                    check_type(dep_module_output, input_type_requirements)
                except TypeCheckError, e:
                    additional_name_str = "".join("->%s" % an for an in additional_names)
                    raise PipelineStructureError("type-checking error matching input '%s' to module '%s' with output "
                                                 "'%s%s' from module '%s': %s" %
                                                 (input_name, self.module_name, output_name, additional_name_str,
                                                  dep_module_name, e))

    def get_software_dependencies(self):
        """
        Check that all software required to execute this module is installed and locatable. This is
        separate to metadata config checks, so that you don't need to satisfy the dependencies for
        all modules in order to be able to run one of them. You might, for example, want to run different
        modules on different machines. This is called when a module is about to be executed and each of the
        dependencies is checked.

        Returns a list of instances of subclasses of :class:~pimlico.core.dependencies.base.SoftwareDependency,
        representing the libraries that this module depends on.

        Take care when providing dependency classes that you don't put any import statements at the top of the Python
        module that will make loading the dependency type itself dependent on runtime dependencies.
        You'll want to run import checks by putting import statements within this method.

        You should call the super method for checking superclass dependencies.

        """
        return []

    def get_input_software_dependencies(self):
        """
        Collects library dependencies from the input datatypes to this module, which will need to be satisfied
        for the module to be run.

        Unlike :meth:`get_software_dependencies`, it shouldn't need to be overridden by subclasses,
        since it just collects the results of getting dependencies from the datatypes.

        """
        # Instantiate any input datatypes this module will need and check the datatype's dependencies
        return sum([
            mod.get_software_dependencies() for input_name in self.inputs.keys()
            for mod in self.get_input(input_name, always_list=True)
        ], [])

    def check_ready_to_run(self):
        """
        Called before a module is run, or if the 'check' command is called. This will only be called after
        all library dependencies have been confirmed ready (see :method:get_software_dependencies).

        Essentially, this covers any module-specific checks that used to be in check_runtime_dependencies()
        other than library installation (e.g. checking models exist).

        Always call the super class' method if you override.

        Returns a list of (name, description) pairs, where the name identifies the problem briefly and the
        description explains what's missing and (ideally) how to fix it.

        """
        # In the base case, there are no problems for this module
        problems = []
        # Check any previous modules that are not executable: their check also need to be satisfied when this one is run
        for dep_module_name in self.dependencies:
            dep_module = self.pipeline[dep_module_name]
            if not dep_module.module_executable:
                problems.extend(dep_module.check_ready_to_run())
        return problems

    def reset_execution(self):
        """
        Remove all output data and metadata from this module to make a fresh start, as if it's never been executed.

        May be overridden if a module has some side effect other than creating/modifying things in its output
        directory(/ies), but overridden methods should always call the super method. Occasionally this is
        necessary, but most of the time the base implementation is enough.

        """
        for path in self.pipeline.find_all_data_paths(self.get_module_output_dir()):
            shutil.rmtree(path)

    def get_detailed_status(self):
        """
        Returns a list of strings, containing detailed information about the module's status that is specific to
        the module type. This may include module-specific information about execution status, for example.

        Subclasses may override this to supply useful (human-readable) information specific to the module type.
        They should called the super method.
        """
        return []

    @classmethod
    def module_package_name(cls):
        """
        The package name for the module, which is used to identify it in config files. This is the
        package containing the info.py in which the ModuleInfo is defined.

        """
        return cls.__module__.rpartition(".info")[0]

    def get_execution_dependency_tree(self):
        """
        Tree of modules that will be executed when this one is executed. Where this module depends on filters,
        the tree goes back through them to find what they depend on (since they will be executed simultaneously)

        """
        inputs = []
        for input_name in self.input_names:
            for previous_module, output_name, additional_names in \
                    self.get_input_module_connection(input_name, always_list=True):
                if previous_module.is_filter():
                    inputs.append((input_name, output_name, previous_module.get_execution_dependency_tree()))
                else:
                    inputs.append((input_name, output_name, (previous_module, [])))
        return self, inputs

    def get_all_executed_modules(self):
        """
        Returns a list of all the modules that will be executed when this one is (including itself).
        This is the current module (if executable), plus any filters used to produce its inputs.

        """
        if self.is_input():
            return []
        else:
            modules = [self]
            for input_name in self.input_names:
                for previous_module, output_name, additional_names in \
                        self.get_input_module_connection(input_name, always_list=True):
                    if previous_module.is_filter():
                        modules.extend(previous_module.get_all_executed_modules())
            return modules

    @property
    def lock_path(self):
        return os.path.join(self.get_module_output_dir(short_term_store=True), ".execution_lock")

    def lock(self):
        """
        Mark the module as locked, so that it cannot be executed. Called when execution begins, to ensure that
        you don't end up executing the same module twice simultaneously.

        """
        with open(self.lock_path, "w") as f:
            f.write("This module cannot be executed, because it is locked")

    def unlock(self):
        """
        Remove the execution lock on this module.

        """
        if os.path.exists(self.lock_path):
            os.remove(self.lock_path)

    def is_locked(self):
        """
        :return: True is the module is currently locked from execution
        """
        return os.path.exists(self.lock_path)


def check_type(provided_type, type_requirements):
    """
    Type-checking algorithm for making sure outputs from modules connect up with inputs that they
    satisfy the requirements for.

    """
    # Input types may be tuples, to allow multiple types
    if type(type_requirements) is not tuple:
        type_requirements = (type_requirements,)
    # Make sure the input type requirements are given in a suitable form
    for intype in type_requirements:
        if not (isinstance(intype, type) and issubclass(intype, PimlicoDatatype)) and \
                not isinstance(intype, DynamicInputDatatypeRequirement):
            # Alternatively, it can be an instance of a dynamic datatype requirement
            raise TypeCheckError("invalid input datatype requirement. Each item must be either a PimlicoDatatype "
                                 "subclass or instance of a DynamicInputDatatypeRequirement subclass: got '%s'" %
                                 type(intype).__name__)

    # Check that the provided output type is a subclass of (or equal to) the required input type
    if not any(_compatible_input_type(intype, provided_type) for intype in type_requirements):
        raise TypeCheckError("required type is %s (or a descendent), but provided type is %s" % (
            "/".join(t.type_checking_name() for t in type_requirements), provided_type.type_checking_name()))


def _compatible_input_type(type_requirement, supplied_type):
    # If the type requirement is just a Pimlico datatype, we check whether the supplied type is a subclass of it
    # Otherwise it's expected to be an instance of a DynamicInputDatatypeRequirement subclass
    # Call check_type() on the supplied type to check whether it's compatible
    return type_requirement.check_type(supplied_type)


class BaseModuleExecutor(object):
    """
    Abstract base class for executors for Pimlico modules. These are classes that actually
    do the work of executing the module on given inputs, writing to given output locations.

    """
    def __init__(self, module_instance_info, stage=None, debug=False, force_rerun=False):
        self.debug = debug
        self.force_rerun = force_rerun
        self.stage = stage
        self.info = module_instance_info
        self.log = module_instance_info.pipeline.log.getChild(module_instance_info.module_name)
        # Work out how many processes we should use
        # Normally just comes from pipeline, but we don't parallelize filters
        self.processes = module_instance_info.pipeline.processes if not module_instance_info.is_filter() else 1

    def execute(self):
        """
        Run the actual module execution.

        May return None, in which case it's assumed to have fully completed. If a string is returned, it's used
        as an alternative module execution status. Used, e.g., by multi-stage modules that need to be run multiple
        times.

        """
        raise NotImplementedError


class ModuleInfoLoadError(Exception):
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        super(ModuleInfoLoadError, self).__init__(*args, **kwargs)


class ModuleExecutorLoadError(Exception):
    pass


class ModuleTypeError(Exception):
    pass


class TypeCheckError(Exception):
    pass


class DependencyError(Exception):
    """
    Raised when a module's dependencies are not satisfied. Generally, this means a dependency library
    needs to be installed, either on the local system or (more often) by calling the appropriate
    make target in the lib directory.

    """
    def __init__(self, message, stderr=None, stdout=None):
        super(DependencyError, self).__init__(message)
        self.stdout = stdout
        self.stderr = stderr


def load_module_executor(path_or_info):
    """
    Utility for loading the executor class for a module from its full path.
    More or less just a wrapper around an import, with some error checking. Locates the executor by a standard
    procedure that involves checking for an "execute" python module alongside the info's module.

    Note that you shouldn't generally use this directly, but instead call the `load_executor()` method on a
    module info (which will call this, unless special behaviour has been defined).

    :param path: path to Python package containing the module
    :return: class
    """
    if isinstance(path_or_info, basestring):
        # First import the metadata class
        module_info = load_module_info(path_or_info)
    else:
        module_info = path_or_info

    # Check this isn't an input module: they shouldn't be executed
    if not module_info.module_executable:
        raise ModuleExecutorLoadError("%s module type is not an executable module. It can't be (and doesn't need "
                                      "to be) executed: execute the next module in the pipeline" %
                                      module_info.module_type_name)
    # Check whether the module provides a special executor before trying to load one in the standard way
    if module_info.module_executor_override is not None:
        return module_info.module_executor_override
    else:
        if isinstance(path_or_info, basestring):
            # Try loading a module called "execute"
            executor_path = "%s.execute" % path_or_info

            try:
                mod = import_module(executor_path)
            except ImportError, e:
                # Executors used to be defined in a module called "exec", until I realised this was stupid, as it's
                #  as reserved word!
                # Check whether one such exists and use it if it does
                try:
                    mod = import_module("%s.exec" % path_or_info)
                except ImportError:
                    # If not, raise an error relating to the new "execute" convention, not the old, deprecated name
                    raise ModuleInfoLoadError("module %s could not be loaded, could not import path %s" %
                                              (path_or_info, executor_path), cause=e)
                else:
                    # Output a deprecation warning so we know to fix this naming
                    warnings.warn("module '%s' uses an 'exec' python module to define its executor. Should be renamed "
                                  "to 'execute'" % path_or_info)
        else:
            # We were given a module info instance: work out where it lives and get the executor relatively
            try:
                mod = import_module("..execute", module_info.__module__)
            except ImportError, e:
                # Check whether an 'exec' module exists
                try:
                    mod = import_module("..exec", module_info.__module__)
                except ImportError:
                    raise ModuleInfoLoadError("module %s could not be loaded, could not import ..execute from "
                                              "ModuleInfo's module, %s" %
                                              (path_or_info, module_info.__module__), cause=e)
                else:
                    # Output a deprecation warning so we know to fix this naming
                    warnings.warn("module '%s' uses an 'exec' python module to define its executor. Should be renamed "
                                  "to 'execute'" % path_or_info.module_package_name)
        if not hasattr(mod, "ModuleExecutor"):
            raise ModuleExecutorLoadError("could not load class %s.ModuleExecutor" % mod.__name__)
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
        raise ModuleInfoLoadError("module type '%s' could not be found (could not import %s)" % (path, info_path))

    if not hasattr(mod, "ModuleInfo"):
        raise ModuleInfoLoadError("invalid module type code: could not load class %s.ModuleInfo" % info_path)
    return mod.ModuleInfo
