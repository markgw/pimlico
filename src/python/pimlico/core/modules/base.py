# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

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
import re
from builtins import zip
import copy
from operator import itemgetter

from future.utils import raise_from
from past.builtins import basestring
from builtins import object

import json
import os
import shutil
import warnings
from datetime import datetime
from importlib import import_module

from tabulate import tabulate

from pimlico.core.config import PipelineStructureError
from pimlico.core.modules.options import process_module_options
from pimlico.datatypes.base import PimlicoDatatype, DynamicOutputDatatype, DynamicInputDatatypeRequirement, \
    MultipleInputs, DataNotReadyError
from pimlico.utils.core import remove_duplicates


class BaseModuleInfo(object):
    """
    Abstract base class for all pipeline modules' metadata.

    """
    module_type_name = None
    module_readable_name = None
    module_options = {}
    module_inputs = []
    """ Specifies a list of (name, datatype instance) pairs for inputs that are always required """
    module_optional_inputs = []
    """ 
    Specifies a list of (name, datatype instance) pairs for optional inputs. The module's execution may 
    vary depending on what is provided. If these are not given, None is returned from get_input() 
    """
    module_outputs = []
    """ Specifies a list of (name, datatype instance) pairs for outputs that are always written """
    module_optional_outputs = []
    """
    Specifies a list of (name, datatype instance) pairs for outputs that are written only if they're specified
    in the "output" option or used by another module
    """
    module_output_groups = []
    """
    List of output groups: (group_name, [output_name1, ...]).
    Further groups may be added by build_output_groups().
    """
    module_executable = True
    """
    Whether the module should be executed
    Typically True for almost all modules, except input modules (though some of them may also require execution) and
    filters
    """
    module_executor_override = None
    """ If specified, this ModuleExecutor class will be used instead of looking one up in the exec Python module """
    main_module = None
    """
    Usually None. In the case of stages of a multi-stage module, stores a pointer to the main module.

    """
    module_supports_python2 = False
    """
    Most core Pimlico modules support use in Python 2 and 3. Modules that do should set 
    this to True. If it is False, the module is assumed to work only in Python 3.
    
    Since Python 2 compatibility requires extra work from the programmer, this is 
    False by default.
    
    To check whether a module can be used in Python 2, call ``supports_python2()``, 
    which will check this and also input and output datatypes.
    
    """

    def __init__(self, module_name, pipeline, inputs={}, options={}, optional_outputs=[],
                 docstring="", include_outputs=[], alt_expanded_from=None, alt_param_settings=[], module_variables={}):
        self.docstring = docstring
        self.inputs = inputs
        self.options = options
        self.module_name = module_name
        self.pipeline = pipeline
        self.module_variables = module_variables
        # If this module instance was created by expanded a module section in the config according to alternative
        # parameter values, this attribute stores the name of the expanded module
        self.alt_expanded_from = alt_expanded_from
        # For alt-expanded modules, this stores a list of tuples (key, (val, name)) representing the values that
        # were assigned to the parameters for this expansion
        # key is the parameter name, val the assigned value and name the name associated with the alternative, if any
        self.alt_param_settings = alt_param_settings

        # Allow the module's list of outputs to be expanded at this point, depending on options and inputs
        self.module_outputs = self.module_outputs + self.provide_further_outputs()

        # Work out what outputs this module will make available
        if len(self.module_outputs + self.module_optional_outputs) == 0:
            self.default_output_name = None
        else:
            self.default_output_name = (self.module_outputs+self.module_optional_outputs)[0][0]

        # The basic outputs are always available
        self.available_outputs = list(self.module_outputs)
        # Replace None with the default output name (which could be an optional output if no non-optional are defined)
        include_outputs = set([n for n in
                               [name if name is not None else self.default_output_name for name in include_outputs]
                               if n is not None])
        # Include all of these outputs in the final output list
        self.available_outputs.extend((name, dt) for (name, dt) in self.module_optional_outputs
                                      if name in set(optional_outputs) | include_outputs)

        # Define output groups, now that the final list of available outputs is available
        self.output_groups = copy.deepcopy(self.module_output_groups) + self.build_output_groups()

        self._metadata = None
        self._history = None
        self.__module_output_dir = None

    def __repr__(self):
        return "%s(%s)" % (self.module_type_name, self.module_name)

    @classmethod
    def supports_python2(cls):
        """
        :return: True if the module can be run in Python 2 and 3, False if it
           only supports Python 3.

        """
        if not cls.module_supports_python2:
            # The module itself does not support Python 2
            return False
        # Also check all the input and output datatypes
        for inout_list in [cls.module_inputs, cls.module_optional_inputs, cls.module_outputs, cls.module_optional_outputs]:
            for inout_name, datatype in inout_list:
                if not datatype.supports_python2():
                    return False
        # Everything supports Python 2 and 3
        return True

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
        return os.path.join(self.pipeline.find_data_path(self.get_module_output_dir(), default="output"), "metadata")

    def get_metadata(self):
        if self._metadata is None:
            # Try loading metadata
            self._metadata = {}
            if os.path.exists(self.metadata_filename):
                with open(self.metadata_filename, "r") as f:
                    data = f.read()
                    if data.strip("\n "):
                        self._metadata = json.loads(data)
        return self._metadata

    def _get_and_prepare_module_output_dir(self):
        # If we've done this before, don't do all the check again, just return a cached value
        if self.__module_output_dir is None:
            self.__module_output_dir = self.get_module_output_dir(absolute=True)
            # Make sure we've got an output directory to output the metadata to
            # Always write to output store, don't search others
            if not os.path.exists(self.__module_output_dir):
                os.makedirs(self.__module_output_dir)
        return self.__module_output_dir

    def set_metadata_value(self, attr, val):
        self.set_metadata_values({attr: val})

    def set_metadata_values(self, val_dict):
        output_dir = self._get_and_prepare_module_output_dir()
        # Load the existing metadata
        metadata = self.get_metadata()
        # Add our new values to it
        metadata.update(val_dict)
        # Write the whole thing out to the file
        with open(os.path.join(output_dir, "metadata"), "w") as f:
            json.dump(metadata, f)

    def __get_status(self):
        # Check the metadata for current module status
        return self.get_metadata().get("status", "UNEXECUTED")

    def __set_status(self, status):
        self.set_metadata_value("status", status)

    status = property(__get_status, __set_status)

    @property
    def execution_history_path(self):
        return os.path.join(self.pipeline.find_data_path(self.get_module_output_dir(), default="output"), "history")

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
        """ All required inputs, first, then all supplied optional inputs """
        return [name for name, __ in self.module_inputs] + \
               [name for name, __ in self.module_optional_inputs if name in self.inputs]

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
    def extract_input_options(cls, opt_dict, module_name=None, previous_module_name=None, module_expansions={}):
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
        :param module_expansions: dictionary mapping module names to a list of expanded module names, where
            expansion has been performed as a result of alternatives in the parameters. Provided here so that
            the unexpanded names may be used to refer to the whole list of module names, where a module takes
            multiple inputs on one input parameter
        :return: dictionary of inputs
        """
        inputs = {}
        for opt_name, opt_value in list(opt_dict.items()):
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
                if input_name not in dict(cls.module_inputs) and input_name not in dict(cls.module_optional_inputs):
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
            input_specs_initial = input_spec.split(",")
            # Check for a * somewhere in the spec other than at the beginning
            # We ignore the case of module_name.*, which denotes all of the module's outputs
            input_specs = []
            input_multipliers = []
            for spec in input_specs_initial:
                # This indicates that one of the inputs should be repeated
                if "*" in spec[1:] and not ".*" in spec:
                    mult_star_idx = spec[1:].index("*") + 1
                    spec, multiplier = spec[:mult_star_idx], spec[mult_star_idx+1:]
                    spec = spec.strip()
                    # We can't do the multiplication now, as the multiplier might be a modvar expression,
                    # or otherwise require further processing
                    input_multipliers.append(multiplier)
                else:
                    # Don't repeat
                    input_multipliers.append("")
                input_specs.append(spec)

            for spec, multiplier in zip(input_specs, input_multipliers):
                # Check for an initial *, meaning we should expand out an expanded previous module input multiple inputs
                if spec.startswith("*"):
                    spec = spec[1:]
                    expand = True
                else:
                    expand = False

                if "[" in spec:
                    # Don't split before the end of the expanded module name
                    part0, part1, rest = spec.partition("[")
                    part2, part3, spec = rest.partition("]")
                    first_part = part0 + part1 + part2 + part3
                else:
                    first_part = ""

                if "." in spec:
                    # This is a module name + output name
                    module_name, __, output_name = spec.rpartition(".")
                else:
                    # Just a module name, using the default output
                    module_name = spec
                    output_name = None
                module_name = first_part + module_name

                if expand:
                    # If the module name starts with a *, it should refer to one that has been expanded out according
                    # to alternatives
                    # If so, treat it as if it were a comma-separated list of inputs, assuming this is a MultipleInputs
                    expanded_module_names = module_expansions.get(module_name, [])
                    if len(expanded_module_names) < 2:
                        # Didn't get the base name of an expanded module -- mistake in config
                        raise ModuleInfoLoadError("input specification '%s' uses *-notation to refer to a previous "
                                                  "module that's been expanded into alternatives, but module '%s' "
                                                  "has not been expanded" % (input_spec, module_name))
                else:
                    expanded_module_names = [module_name]

                # Most of the time there will only be one of these, == module_name
                for expanded_module_name in expanded_module_names:
                    inputs[input_name].append((expanded_module_name, output_name, multiplier))

        return inputs

    @staticmethod
    def choose_optional_outputs_from_options(options, inputs):
        """
        Normally, which optional outputs get produced by a module depend on the 'output' option given in the
        config file, plus any outputs that get used by subsequent modules. By overriding this method, module
        types can add extra outputs into the list of those to be included, conditional on other options.

        It also receives the processed dictionary of inputs, so that the additional outputs can depend on
        what is fed into the input.

        E.g. the corenlp module include the 'annotations' output if annotators are specified, so that the
        user doesn't need to give both options.

        Note that this does not provide additional output definitions, just a list of the optional
        outputs (already defined) that should be included among the outputs produced.

        """
        return []

    # For backwards compatibility: name now changed to clearer version
    get_extra_outputs_from_options = choose_optional_outputs_from_options

    def provide_further_outputs(self):
        """
        Called during instantiation, once inputs and options are available, to add a further list of module
        outputs that are dependent on inputs or options.

        When overriding this, you can provide a new docstring, which will be used in the
        module docs to describe the extra conditional outputs that are added.

        """
        return []

    def build_output_groups(self):
        """
        Called during instantiation to produce a list of named groups of outputs. The list
        extends the statically define output groups in ``module_output_groups``.
        You should use the static list unless you need to override this for conditionally
        added outputs.

        Called after all input, options and output processing has been done, so the
        outputs in the attribute ``available_outputs`` are the final list of outputs that
        this module instance has.

        Returns a list of groups, each specified as: ``(group_name, [output_name1, ...])``.

        May contain as many groups as necessary. They are not required to cover all the
        outputs and outputs may feature in multiple groups.

        Should not include group "all", which is always included by default.

        If you override this, use the docstring to specify what output groups will get
        added and how they are named. The text will be used in the generated module
        docs.

        """
        return []

    def is_output_group_name(self, group_name):
        return group_name == "all" or group_name in dict(self.output_groups)

    def get_output_group(self, group_name):
        """
        Get the list of output names corresponding to the given output group name.

        Raises a KeyError if the output group does not exist.

        """
        if group_name == "all":
            return [name for (name, outtype) in self.available_outputs]
        return dict(self.output_groups)[group_name]

    def get_module_output_dir(self, absolute=False, short_term_store=None):
        """
        Gets the path to the base output dir to be used by this module, relative to the storage base dir.
        When outputting data, the storage base dir will always be the short term store path, but when looking
        for the output data other base paths might be explored, including the long term store.

        Kwarg ``short_term_store`` is included for backward compatibility, but outputs a deprecation warning.

        :param absolute: if True, return absolute path to output dir in output store
        :return: path, relative to store base path, or if absolute=True absolute path to output dir
        """
        if short_term_store is not None:
            warnings.warn("short_term_store kwarg to get_module_output_dir() is deprecated. Use 'absolute' instead")
            # If this was given, it should override absolute, to preserve earlier functionality
            absolute = short_term_store

        relative_dir = self.module_name
        if absolute:
            return os.path.join(self.pipeline.output_path, relative_dir)
        else:
            return relative_dir

    def get_absolute_output_dir(self, output_name):
        """
        The simplest way to get hold of the directory to use to output data to for a given output. This is
        the usual way to get an output directory for an output writer.

        The directory is an absolute path to a location in the Pimlico output storage location.

        :param output_name: the name of an output
        :return: the absolute path to the output directory to use for the named output
        """
        return self.get_output_dir(output_name, absolute=True)

    def get_output_dir(self, output_name, absolute=False, short_term_store=None):
        """
        Kwarg ``short_term_store`` is included for backward compatibility, but outputs a deprecation warning.

        :param absolute: return an absolute path in the storage location used for output. If False (default), return a
            relative path, specified relative to the root of the Pimlico store used. This allows multiple stores
            to be searched for output
        :param output_name: the name of an output
        :return: the path to the output directory to use for the named output, which may be relative to the root
            of the Pimlico store in use (default) or an absolute path in the output store, depending on
            `absolute`

        """
        if short_term_store is not None:
            warnings.warn("short_term_store kwarg to get_output_dir() is deprecated. Use 'absolute' instead")
            # If this was given, it should override absolute, to preserve earlier functionality
            absolute = short_term_store

        if output_name is None:
            output_name = self.default_output_name
            if output_name is None:
                raise PipelineStructureError("{} module has no default output".format(self.module_type_name))

        if output_name not in self.output_names:
            raise PipelineStructureError("%s module does not have an output named '%s'. Available outputs: %s" %
                                         (self.module_type_name, output_name, ", ".join(self.output_names)))

        return os.path.join(self.get_module_output_dir(absolute=absolute), output_name)

    def get_output_datatype(self, output_name=None):
        """
        Get the datatype of a named output, or the default output.
        Returns an instance of the relevant PimlicoDatatype subclass. This can be used
        for typechecking and also for getting a reader for the output data, once it's ready,
        by supplying it with the path to the data.

        To get a reader for the output data, use :meth:`get_output`.

        :param output_name: output whose datatype to retrieve. Default output if not specified
        :return:
        """
        if output_name is None:
            # Get the default output
            # Often there'll be only one output, so a name needn't be specified
            # If there are multiple, the first is the default
            output_name = self.default_output_name
            if output_name is None:
                raise PipelineStructureError("{} module has no default output".format(self.module_type_name))

        outputs = dict(self.available_outputs)
        if output_name not in outputs:
            raise PipelineStructureError("%s module does not have an output named '%s'. Available outputs: %s" %
                                         (self.module_type_name, output_name, ", ".join(outputs.keys())))
        datatype = outputs[output_name]

        # The datatype might be a dynamic type -- with a function that we call to get the type
        if isinstance(datatype, DynamicOutputDatatype):
            # Call the get_datatype() method to build the actual datatype
            datatype = datatype.get_datatype(self)

        # An output datatype should never be a DynamicInputDatatypeRequirement, which should only be used for inputs
        # If this happens, it's an error in the module info definition
        # Since it's an easy mistake to make, check for it here
        if isinstance(datatype, DynamicInputDatatypeRequirement):
            raise PipelineStructureError("error in module info definition for module type '{}': dynamic "
                                         "input type requirement as output type on output '{}'".format(
                self.module_type_name, output_name))

        return output_name, datatype

    def output_ready(self, output_name=None):
        """
        Check whether the named output is ready to be read from one of its possible storage locations.

        :param output_name: output to check, or default output if not given
        :return: False if data is not ready to be read
        """
        reader_setup = self.get_output_reader_setup(output_name)
        return reader_setup.ready_to_read()

    def instantiate_output_reader_setup(self, output_name, datatype):
        """
        Produce a reader setup instance that will be used to prepare this reader.
        This provides functionality like checking that the data is ready to be
        read before the reader is instantiated.

        The standard implementation uses the datatype's methods to get its
        standard reader setup and reader, but some modules may need to override
        this to provide other readers.

        `output_name` is provided so that overriding methods' behaviour can
        be conditioned on which output is being fetched.

        """
        # Get the module's output dir relative to the storage location in use
        dataset_rel_dir = self.get_output_dir(output_name)
        # Get all possible absolute paths where this could be, according to the pipeline's configuration
        possible_paths = [path for (name, path) in self.pipeline.get_data_search_paths(dataset_rel_dir)]
        # Produce a reader setup that will look in these paths for the data
        return datatype(possible_paths)

    def instantiate_output_reader(self, output_name, datatype, pipeline, module=None):
        """
        Prepare a reader for a particular output. The default implementation is
        very simple, but subclasses may override this for cases where the normal
        process of creating readers has to be modified.

        :param output_name: output to produce a reader for
        :param datatype: the datatype for this output, already inferred
        """
        return self.instantiate_output_reader_setup(output_name, datatype).get_reader(pipeline, module=module)

    def get_output_reader_setup(self, output_name=None):
        # Get the datatype for this output
        output_name, datatype = self.get_output_datatype(output_name=output_name)
        # Instantiate a setup for this reader
        return self.instantiate_output_reader_setup(output_name, datatype)

    def get_output(self, output_name=None):
        """
        Get a reader corresponding to one of the outputs of the module. The reader
        will be that which corresponds to the output's declared datatype and
        will read the data from any of the possible locations where it can be
        found.

        If the data is not available in any location, raises a
        :class:`~pimlico.datatypes.base.DataNotReadyError`.

        To check whether the data is ready without calling this, call `output_ready()`.

        """
        reader_setup = self.get_output_reader_setup(output_name)
        # Make sure the data is ready to read before creating the reader
        if not reader_setup.ready_to_read():
            raise DataNotReadyError("tried to get reader for output '{}' to module '{}', but data is not "
                                    "ready to read yet".format(output_name or "default", self.module_name))
        return reader_setup(self.pipeline, module=self.module_name)

    def get_output_writer(self, output_name=None, **kwargs):
        """
        Get a writer instance for the given output. Kwargs will be passed through to the
        writer and used to specify metadata and writer params.

        :param output_name: output to get writer for, or default output if left
        :param kwargs:
        :return:
        """
        output_name, datatype = self.get_output_datatype(output_name=output_name)
        return datatype.get_writer(
            self.get_output_dir(output_name, absolute=True),
            self.pipeline,
            self.module_name,
            **kwargs
        )

    def is_multiple_input(self, input_name=None):
        """
        Returns True if the named input (or default input if no name is given) is a MultipleInputs input, False
        otherwise. If it is, get_input() will return a list, otherwise it will return a single datatype.

        """
        if input_name is None:
            input_type = self.module_inputs[0][1]
        else:
            input_type = dict(self.module_inputs + self.module_optional_inputs)[input_name]
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
            if len(self.module_inputs):
                input_name = self.module_inputs[0][0]
            else:
                raise PipelineStructureError("module '%s' doesn't have any inputs. Tried to get the first input" %
                                             self.module_name)
        if input_name not in self.inputs:
            # Check whether it's an optional input that's not been given, so we can say so in the error
            if input_name in dict(self.module_optional_inputs):
                raise PipelineStructureError("could not get optional input '{}' to module '{}', as it's not "
                                             "been given".format(input_name, self.module_name))
            else:
                raise PipelineStructureError("module '%s' doesn't have an input '%s'" % (self.module_name, input_name))

        # Try getting hold of the module that we need the output of
        if always_list or self.is_multiple_input(input_name):
            return [(self.pipeline[previous_module_name], output_name)
                    for (previous_module_name, output_name) in self.inputs[input_name]]
        else:
            previous_module_name, output_name = self.inputs[input_name][0]
            return self.pipeline[previous_module_name], output_name

    def get_input_datatype(self, input_name=None, always_list=False):
        """
        Get a list of datatype instances corresponding to one of the inputs to the module.
        If an input name is not given, the first input is returned.

        If the input type was specified with MultipleInputs, meaning that we're expecting an unbounded number
        of inputs, this is a list. Otherwise, it's a single datatype.

        """
        datatypes = [
            previous_module.get_output_datatype(output_name)[1]
            for previous_module, output_name in self.get_input_module_connection(input_name, always_list=True)
        ]
        return datatypes if always_list or self.is_multiple_input(input_name) else datatypes[0]

    def get_input_reader_setup(self, input_name=None, always_list=False):
        """
        Get reader setup for one of the inputs to the module.
        Looks up the corresponding output from another module and uses that module's metadata to
        get that output's instance.
        If an input name is not given, the first input is returned.

        If the input type was specified with MultipleInputs, meaning that we're expecting an unbounded number
        of inputs, this is a list. Otherwise, it's a single datatype instance.
        If always_list=True, in this latter case we return a single-item list.

        If the requested input name is an optional input and it has not been supplied,
        returns None.

        You can get a reader for the input, once the data is ready to be read, by
        calling `get_reader()` on the setup object. Or use `get_input()` on the module.

        """
        # Check whether this is an optional input: otherwise get_input_module_connection() will raise an error
        if input_name is not None and input_name in dict(self.module_optional_inputs) and input_name not in self.inputs:
            return None

        inputs = [
            previous_module.get_output_reader_setup(output_name)
            for previous_module, output_name in self.get_input_module_connection(input_name, always_list=True)
        ]
        return inputs if always_list or self.is_multiple_input(input_name) else inputs[0]

    def get_input(self, input_name=None, always_list=False):
        """
        Get a reader for one of the inputs to the module. Should only be called once
        the input data is ready to read. It's therefore fine to call this from a
        module executor, since data availability has already been checked by
        this point.

        If the input type was specified with :class:`~pimlico.datatypes.base.MultipleInputs`,
        meaning that we're expecting an unbounded number
        of inputs, this is a list. Otherwise, it's a single datatype instance.
        If ``always_list=True``, in this latter case we return a single-item list.

        If the requested input name is an optional input and it has not been supplied,
        returns None.

        Similarly, if you run in preliminary mode, multiple inputs might produce None
        for some of their inputs if the data is not ready.

        """
        input_setups = self.get_input_reader_setup(input_name=input_name, always_list=always_list)
        if input_setups is None:
            return None
        if type(input_setups) is list:
            readers = [
                # Usually, the data must be ready to read before we get this far
                # But, if running in preliminary mode, some inputs might not be ready and should return None
                setup.get_reader(self.pipeline, self.module_name) if setup.ready_to_read() else None
                for setup in input_setups if setup is not None
            ]
            if len(readers) == 0:
                return None
            else:
                return readers
        else:
            return input_setups.get_reader(self.pipeline, self.module_name)

    def input_ready(self, input_name=None):
        """
        Check whether the data is ready to go corresponding to the named input.

        :param input_name: input to check
        :return: True if input is ready
        """
        return len(self.missing_data([input_name])) == 0

    def all_inputs_ready(self):
        """
        Check `input_ready()` on all inputs.

        :return: True if all input datatypes are ready to be used
        """
        return len(self.missing_data()) == 0 and len(self.missing_module_data()) == 0

    @classmethod
    def is_filter(cls):
        return not cls.module_executable and len(cls.module_inputs) > 0

    def missing_module_data(self):
        """
        Reports missing data not associated with an input dataset.

        Calling `missing_data()` reports any problems with input data associated with a particular input to
        this module. However, modules may also rely on data that does not come from one of their inputs. This
        happens primarily (perhaps solely) when a module option points to a data source. This might be the
        case with any module, but is particularly common among input reader modules, which have no inputs, but
        read data according to their options.

        :return: list of problems
        """
        return []

    def missing_data(self, input_names=None, assume_executed=[], assume_failed=[], allow_preliminary=False):
        """
        Check whether all the input data for this module is available. If not, return a list strings indicating
        which outputs of which modules are not available. If it's all ready, returns an empty list.

        To check specific inputs, give a list of input names. To check all inputs, don't specify `input_names`.
        To check the default input, give `input_names=[None]`. If not checking a specific input, also checks
        non-input data (see `missing_module_data()`).

        If `assume_executed` is given, it should be a list of module names which may be assumed to have been
        executed at the point when this module is executed. Any outputs from those modules will be excluded from
        the input checks for this module, on the assumption that they will have become available, even if they're
        not currently available, by the time they're needed.

        If `assume_executed` is given, it should be a list of module names which should be assumed to have failed.
        If we rely on data from the output of one of them, instead of checking whether it's available we simply
        assume it's not.

        Why do this? When running multiple modules in sequence, if one fails it is possible that its output datasets
        look like complete datasets. For example, a partially written iterable corpus may look like a perfectly
        valid corpus, which happens to be smaller than it should be. After the execution failure, we may check other
        modules to see whether it's possible to run them. Then we need to know not to trust the output data from the
        failed module, even if it looks valid.

        If `allow_preliminary=True`, for any inputs that are multiple inputs and have multiple connections to
        previous modules, consider them to be satisfied if at least one of their inputs is ready. The normal
        behaviour is to require all of them to be ready, but in a preliminary run this requirement is relaxed.

        """
        from pimlico.core.modules.multistage import MultistageModuleInfo

        missing = []
        if input_names is None:
            # Default to checking all inputs
            input_names = self.input_names
            # Also check module data (non-input data)
            missing.extend(self.missing_module_data())
        if not self.is_input():
            # Don't check inputs for an input module: there aren't any
            # If checks need to be performed before an input module's data preparation is run (i.e. an
            # executable input module), they are added by overriding this method

            for input_name in input_names:
                input_connections = self.get_input_module_connection(input_name, always_list=True)
                missing_for_input = []

                # If an input connection comes from a multistage module, we need to replace it with its relevant stage
                for previous_module, output_name in input_connections:
                    # If the previous module is to be assumed executed, skip checking anything
                    if previous_module.module_name in assume_executed:
                        continue

                _input_connections = copy.copy(input_connections)
                input_connections = []
                for (previous_module, output_name) in _input_connections:
                    if isinstance(previous_module, MultistageModuleInfo):
                        if output_name is None:
                            # Get the default output name
                            # TODO Is this the correct way to do this??
                            output_name = previous_module.available_outputs[0][0]
                        ms_stage, ms_stage_output = previous_module.module_output_stage_names[output_name]
                        input_connections.append((
                            # The pipeline module for the substage
                            previous_module.named_internal_modules[ms_stage],
                            # The output from that module that we need
                            ms_stage_output
                        ))
                    else:
                        input_connections.append((previous_module, output_name))

                for previous_module, output_name in input_connections:
                    # If the previous module is to be assumed executed, skip checking whether its output data is
                    # available
                    if previous_module.module_name in assume_executed:
                        continue
                    # Check whether we can get the output reader for the output corresponding to this input
                    reader_setup = previous_module.get_output_reader_setup(output_name)
                    if not reader_setup.ready_to_read():
                        # If the previous module is a filter, it's more helpful to say exactly what data it's missing
                        if previous_module.is_filter():
                            missing_for_input.extend(previous_module.missing_data(assume_executed=assume_executed))
                        else:
                            if output_name is None:
                                missing_for_input.append("%s (default output)" % previous_module.module_name)
                            else:
                                missing_for_input.append("%s output '%s'" % (previous_module.module_name, output_name))
                    else:
                        if previous_module.module_name in assume_failed:
                            # If previous module is assumed failed, assume its output data is not ready,
                            # even when it looks ready
                            missing_for_input.append("%s module failed, so we assume  output '%s' is not complete" %
                                                     (previous_module.module_name, output_name))

                if allow_preliminary and len(input_connections) > 1:
                    # For multiple inputs, be satisfied with at least one ready
                    if len(missing_for_input) < len(input_connections):
                        # At least one has no problem: this will do
                        continue
                    else:
                        # Add all of the individual problems
                        missing.extend([
                            "preliminary run requires at least one input ready: %s" % mess for mess in missing_for_input
                        ])
                else:
                    # Normal behaviour: report all input problems
                    missing.extend(missing_for_input)
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
             for (module_name, output_name) in input_connections])

    def get_transitive_dependencies(self):
        """
        Transitive closure of `dependencies`.

        :return: list of names of modules that this one recursively (transitively) depends on for its inputs.
        """
        deps = self.dependencies
        for dep in deps:
            deps.extend(self.pipeline[dep].get_transitive_dependencies())
        return remove_duplicates(deps)

    def typecheck_inputs(self):
        if self.is_input() or len(self.module_inputs) == 0:
            # Nothing to check
            return

        for input_name in self.inputs.keys():
            # Check the type of each input in turn
            # This raises an exception if typechecking fails, which we let get passed up
            self.typecheck_input(input_name)

    def typecheck_input(self, input_name):
        """
        Typecheck a single input. ``typecheck_inputs()`` calls this and is used for
        typechecking of a pipeline. This method returns the (or the first) satisfied input
        requirement, or raises an exception if typechecking failed, so can be handy separately to
        establish which requirement was met.

        The result is always a list, but will contain only one item unless the input is a multiple
        input.

        """
        input_connections = self.inputs[input_name]
        input_type_requirements = dict(self.module_inputs + self.module_optional_inputs)[input_name]

        if isinstance(input_type_requirements, MultipleInputs):
            # Type requirements are the same for all inputs
            input_type_requirements = input_type_requirements.datatype_requirements
        elif len(input_connections) > 1:
            # Doesn't accept multiple datatypes on a single input, so shouldn't have more than one
            raise PipelineStructureError("input %s on module '%s' does not accept multiple inputs, but %d were "
                                         "given" % (input_name, self.module_name, len(input_connections)))

        first_satisfied = []
        for dep_module_name, output_name in input_connections:
            # Load the dependent module
            dep_module = self.pipeline[dep_module_name]
            # Try to load the named output (or the default, if no name was given)
            dep_module_output_name, dep_module_output = dep_module.get_output_datatype(output_name=output_name)

            # Check the output datatype is given in a suitable form
            if not isinstance(dep_module_output, (DynamicOutputDatatype, PimlicoDatatype)):
                raise PipelineStructureError(
                    "invalid output datatype from output '{}' of module '{}'. Must be instance of PimlicoDatatype "
                    "subclass or a DynamicOutputDatatype subclass, got {}".format(
                        dep_module_output_name, dep_module_name, type(dep_module_output).__name__
                    ),
                    explanation="type({}.{}): {}".format(
                        dep_module_name, dep_module_output_name, type(dep_module_output)
                    )
                )
            try:
                first_satisfied.append(check_type(dep_module_output, input_type_requirements))
            except TypeCheckError as e:
                e.input = "{}.{}".format(self.module_name, input_name)
                e.source = "{}.{}".format(dep_module_name, output_name or "[default]")
                raise PipelineStructureError(
                    "type-checking error matching input '{}' to module '{}' with output '{}' from "
                    "module '{}': {}".format(
                        input_name, self.module_name, output_name or "default", dep_module_name, e
                    ),
                    explanation=e.format(),
                )
        return first_satisfied

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
            dtype.get_software_dependencies() for input_name in self.inputs.keys()
            for dtype in self.get_input_datatype(input_name, always_list=True)
        ], [])

    def get_output_software_dependencies(self):
        """
        Collects library dependencies from the output datatypes to this module, which will need to be satisfied
        for the module to be run.

        Unlike :meth:`get_input_software_dependencies`, it may not be the case that all of these dependencies
        strictly need to be satisfied before the module can be run. It could be that a datatype can be written
        without satisfying all the dependencies needed to read it. However, we assume that dependencies of all
        output datatypes must be satisfied in order to run the module that writes them, since this is usually
        the case, and these are checked before running the module.

        Unlike :meth:`get_software_dependencies`, it shouldn't need to be overridden by subclasses,
        since it just collects the results of getting dependencies from the datatypes.

        """
        # Instantiate any output datatypes this module will need and check the datatype's dependencies
        dtypes = [
            self.get_output_datatype(output_name)[1]
            for output_name, __ in self.available_outputs
        ]
        # Get dependencies for each datatype, plus the additional dependencies
        # declared to apply to the writer specifically, since we're writing here
        return sum([
            dtype.get_software_dependencies() + dtype.get_writer_software_dependencies()
            for dtype in dtypes
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
        for name, path in self.pipeline.get_data_search_paths(self.get_module_output_dir()):
            if os.path.exists(path):
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
            for previous_module, output_name in \
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
                for previous_module, output_name in \
                        self.get_input_module_connection(input_name, always_list=True):
                    if previous_module.is_filter():
                        modules.extend(previous_module.get_all_executed_modules())
            return modules

    @property
    def lock_path(self):
        return os.path.join(self.get_module_output_dir(absolute=True), ".execution_lock")

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

    def get_log_filenames(self, name="error"):
        """
        Get a list of all the log filenames of the given prefix that exist in the module's
        output dir. They will be ordered according to their numerical suffixes (i.e. the
        order in which they were created).

        Returns a list of (filename, num) tuples, where num is the numerical suffix as an int.

        """
        dir_name = self.get_module_output_dir(absolute=True)
        if not os.path.exists(dir_name):
            # No log files, as there's no output dir
            return []
        # Search for all filenames of the right form
        pattern = re.compile(r"{}(\d\d\d).log".format(name))
        found = []
        for module_file in os.listdir(dir_name):
            m = pattern.match(module_file)
            if m is not None:
                file_number = int(m.group(1))
                found.append((module_file, file_number))
        found.sort(key=itemgetter(1))
        return found

    def get_new_log_filename(self, name="error"):
        """
        Returns an absolute path that can be used to output a log file for this module. This is used for
        outputting error logs. It will always return a filename that doesn't currently exist, so can be used
        multiple times to output multiple logs.

        """
        dir_name = self.get_module_output_dir(absolute=True)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        # Search for a filename that doesn't already exist
        old_files = self.get_log_filenames(name)
        if len(old_files) == 0:
            file_number = 0
        else:
            file_number = old_files[-1][1] + 1
        filename = "{}{:03d}.log".format(name, file_number)
        return os.path.join(dir_name, filename)

    def get_last_log_filename(self, name="error"):
        """
        Get the most recent error log that was created by a call to get_new_log_filename().
        Returns an absolute path, or None if no matching files are found.

        """
        old_files = self.get_log_filenames(name)
        if len(old_files) == 0:
            return None
        else:
            return os.path.join(self.get_module_output_dir(absolute=True), old_files[-1][0])

def collect_unexecuted_dependencies(modules):
    """
    Given a list of modules, checks through all the modules that they depend on to put together a list of
    modules that need to be executed so that the given list will be left in an executed state. The list
    includes the modules themselves, if they're not fully executed, and unexecuted dependencies of any
    unexecuted modules (recursively).

    :param modules: list of ModuleInfo instances
    :return: list of ModuleInfo instances that need to be executed
    """
    from pimlico.core.modules.multistage import MultistageModuleInfo

    if len(modules) == 0:
        return []
    else:
        pipeline = modules[0].pipeline

        def _get_deps(mod):
            # If it's not executable, don't add it, but do recurse
            # If it's not completed, recurse and add
            if not mod.module_executable or mod.status != "COMPLETE":
                unex_mods = []
                # Add all of this module's unexecuted deps to the list first
                for dep_name in mod.dependencies:
                    dep = pipeline[dep_name]
                    # If we get a multistage module, then we add dependencies on all its stages (instead)
                    # We could also check more specifically for the stages that we actually need, but
                    # this becomes a bit more difficult, so for now we take this simpler approach
                    if isinstance(dep, MultistageModuleInfo):
                        for internal_mod in dep.internal_modules:
                            unex_mods.extend(_get_deps(internal_mod))
                    else:
                        unex_mods.extend(_get_deps(dep))
                if mod.module_executable:
                    # Now add the module itself
                    unex_mods.append(mod)
                return unex_mods
            else:
                # Executable module that's been fully executed
                return []

        # Get the full tree of dependencies for this module by depth-first search
        # This can include duplicates
        modules_to_execute = sum((_get_deps(m) for m in modules), [])

        # If we now remove duplicates, including the first occurrence of each module,
        # we guarantee that each module comes after all its dependencies
        modules_to_execute = remove_duplicates(modules_to_execute, key=lambda m: m.module_name)
        return modules_to_execute


def collect_runnable_modules(pipeline, preliminary=False):
    """
    Look for all unexecuted modules in the pipeline to find any that are ready to be executed. Keep
    collecting runnable modules, including those that will become runnable once we've run earlier ones
    in the list, to produce a list of a sequence of modules that could be set running now.

    :param pipeline: pipeline config
    :return: ordered list of runable modules. Note that it must be run in this order, as some might
        depend on earlier ones in the list
    """
    runnable_modules = []

    # Go through the modules in order: modules can't depend on modules later in the pipeline
    for module_name in pipeline.modules:
        module = pipeline[module_name]
        if module.module_executable and module.status != "COMPLETE":
            # Executable module that's not been completed yet
            # See whether it's ready to run
            if not module.missing_data(assume_executed=runnable_modules, allow_preliminary=preliminary):
                # This module's ready, or will be by the time we get here
                runnable_modules.append(module_name)
    return runnable_modules


def satisfies_typecheck(provided_type, type_requirements):
    """
    Interface to Pimlico's standard type checking (see `check_type`) that returns a boolean to say whether
    type checking succeeded or not.

    """
    try:
        check_type(provided_type, type_requirements)
    except TypeCheckError:
        return False
    return True


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
        if not isinstance(intype, (PimlicoDatatype, DynamicInputDatatypeRequirement)):
            # Alternatively, it can be an instance of a dynamic datatype requirement
            raise TypeCheckError("invalid input datatype requirement. Must be either a PimlicoDatatype or "
                                 "DynamicInputDatatypeRequirement  instance: got '%s'" %
                                 type(intype).__name__)

    # Check that the provided output type is a subclass of (or equal to) the required input type
    for intype in type_requirements:
        if _compatible_input_type(intype, provided_type):
            # Return the requirement that was met, which is handy in some circumstances
            return intype
    # No requirement was met
    # Try to use type_checking_name() to identify types
    provided_type_name = type_checking_name(provided_type)
    req_types = "/".join(type_checking_name(t) for t in type_requirements)
    raise TypeCheckError(
        "required type is {} (or a descendent), but provided type is {}".format(req_types, provided_type_name),
        required_type=req_types,
        provided_type=provided_type_name,
    )


def type_checking_name(typ):
    try:
        return typ.type_checking_name()
    except AttributeError:
        if not hasattr(typ, "type_checking_name"):
            return "{} (no type_checking_name for type)".format(type(typ).__name__)
        else:
            raise


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
    """
    Pipeline type-check mismatch.

    Full description of problem provided in error message.
    May optionally provide more detailed information about the input and output (source)
    that failed to match, the expected type and the received type, all as strings.
    Specify using kwargs ``input``, ``source``, ``required_type`` and
    ``provided_type``.

    """
    def __init__(self, *args, **kwargs):
        self.input = kwargs.pop("input_desc", None)
        self.source = kwargs.pop("output_desc", None)
        self.provided_type = kwargs.pop("provided_type", None)
        self.required_type = kwargs.pop("required_type", None)
        super(TypeCheckError, self).__init__(*args, **kwargs)

    def format(self):
        """
        Provide a nice visual format of the mismatch to help the user.

        """
        if any(x is None for x in [self.input, self.source, self.provided_type, self.required_type]):
            return None
        return "Type mismatch:\n{}".format(
            tabulate([
                [" ", "Connection:", self.source, "->", self.input],
                [" ", "Types:", "!> {} <!".format(self.provided_type), "->", self.required_type]
            ], tablefmt="plain", colalign=[None, "left", "right", "center", "left"])
        )


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
            except ImportError as e:
                # If not, raise an error relating to the new "execute" convention, not the old, deprecated name
                raise ModuleInfoLoadError("module %s could not be loaded, could not import path %s" %
                                          (path_or_info, executor_path), cause=e)
        else:
            # We were given a module info instance: work out where it lives and get the executor relatively
            try:
                mod = import_module("..execute", module_info.__module__)
            except ImportError as e:
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
    except ImportError as e:
        raise_from(
            ModuleInfoLoadError("module type '%s' could not be found (could not import %s: %s)" % (path, info_path, e)),
            e
        )

    if not hasattr(mod, "ModuleInfo"):
        raise ModuleInfoLoadError("invalid module type code: could not load class %s.ModuleInfo" % info_path)
    return mod.ModuleInfo
