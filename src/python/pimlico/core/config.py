# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Reading of pipeline config from a file into the data structure used to run and manipulate the pipeline's data.
"""
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library

standard_library.install_aliases()
from builtins import map
from builtins import input
from builtins import zip
from builtins import next
from builtins import str
from builtins import range
from past.builtins import basestring
from builtins import object

import configparser
import copy
import os
import re
import sys
import textwrap
import warnings
import io

from configparser import RawConfigParser, ConfigParser
from collections import OrderedDict
from operator import itemgetter
from socket import gethostname

from pimlico import PIMLICO_ROOT, PROJECT_ROOT, OUTPUT_DIR, TEST_DATA_DIR
from pimlico.cli.debug.stepper import enable_step_for_pipeline
from pimlico.core.dependencies.base import check_and_install
from pimlico.datatypes.base import DatatypeLoadError
from pimlico.datatypes import load_datatype
from pimlico.utils.core import remove_duplicates
from pimlico.utils.format import title_box
from pimlico.utils.logging import get_console_logger

__all__ = [
    "PipelineConfig", "PipelineConfigParseError", "PipelineStructureError", "preprocess_config_file",
    "check_for_cycles", "check_release", "check_pipeline", "get_dependencies", "print_missing_dependencies",
    "print_dependency_leaf_problems", "PipelineCheckError",
]

REQUIRED_LOCAL_CONFIG = []


class PipelineConfig(object):
    """
    Main configuration for a pipeline, read in from a config file.

    For details on how to write config files that get read by this class, see :doc:`/core/config`.

    """
    def __init__(self, name, pipeline_config, local_config,
                 filename=None, variant="main", available_variants=[], log=None, all_filenames=None,
                 module_aliases={}, local_config_sources=None):
        if log is None:
            log = get_console_logger("Pimlico")
        self.log = log

        self.available_variants = available_variants
        self.variant = variant
        self.local_config = local_config
        self.pipeline_config = pipeline_config
        self.filename = filename
        self.all_filenames = all_filenames or [filename]
        self.name = name
        self.module_aliases = module_aliases
        # For debugging purposes, so we can trace where config was loaded from
        self.local_config_sources = local_config_sources

        # Pipeline is empty to start with
        self.module_infos = {}
        self.module_order = []
        self.expanded_modules = {}

        # Certain standard system-wide settings, loaded from the local config
        self.storage_locations = []
        if "store" in local_config:
            # Default, unnamed storage location: use name "default"
            self.storage_locations.append(
                ("default", os.path.join(self.local_config["store"], self.name, self.variant)))
        self.storage_locations.extend([
            (key[6:], os.path.join(val, self.name, self.variant))
            for (key, val) in local_config.items() if key.startswith("store_")
        ])
        if len(self.storage_locations) == 0:
            raise PipelineConfigParseError("at least one storage location must be specified: none found in "
                                           "local config")

        # Number of processes to use for anything that supports multiprocessing
        self.processes = int(self.local_config.get("processes", 1))

        # By default, the first storage location is used for output
        # This may be overridden by storage_location kwarg (which it will later be possible to set from the cmd line)
        self.output_store = self.storage_locations[0][0]

        # Get paths to add to the python path for the pipeline
        # Used so that a project can specify custom module types and other python code outside the pimlico source tree
        if "python_path" in self.pipeline_config:
            # Paths should all be specified relative to the config file's directory
            additional_paths = [self.path_relative_to_config(path) for path in
                                self.pipeline_config["python_path"].split(":") if path]
            # Add these paths for the python path, so later code will be able to import things from them
            sys.path.extend(additional_paths)

        # Step mode is disabled by default: see method enable_step()
        self._stepper = None

        self._module_schedule = None

        self._dependency_cache = None
        self._dependent_cache = None

    def __repr__(self):
        return u"<PipelineConfig '%s'%s>" % (
            self.name,
            u", variant '%s'" % self.variant if self.variant != "main" else ""
        )

    @property
    def modules(self):
        """ List of module names, in the order they were specified in the config file. """
        return self.module_order

    def __getitem__(self, item):
        if item in self.module_aliases:
            return self[self.module_aliases[item]]
        else:
            return self.module_infos[item]

    def __contains__(self, item):
        return item in self.module_infos or item in self.module_aliases

    def __iter__(self):
        for module_name in self.module_order:
            yield self[module_name]

    @property
    def module_dependencies(self):
        """
        Dictionary mapping a module name to a list of the names of modules that it depends on for its inputs.
        """
        if self._dependency_cache is None:
            self._dependency_cache = dict(
                (module_name, self[module_name].dependencies) for module_name in self.modules
            )
        return self._dependency_cache

    @property
    def module_dependents(self):
        """
        Opposite of module_dependencies. Returns a mapping from module names to a list of modules the depend
        on the module.
        """
        if self._dependent_cache is None:
            self._dependent_cache = {}
            # Use the module_dependencies mapping by simply reversing it
            for module_name, dependencies in self.module_dependencies.items():
                for dep in dependencies:
                    self._dependent_cache.setdefault(dep, []).append(module_name)
        return self._dependent_cache

    def get_dependent_modules(self, module_name, recurse=False, exclude=[]):
        """
        Return a list of the names of modules that depend on the named module for their inputs.

        If `exclude` is given, we don't perform a recursive call on any of the modules in the list.
        For each item we recurse on, we extend the exclude list in the recursive call
        to include everything found so far (in other recursive calls). This avoids unnecessary recursion in
        complex pipelines.

        If `exclude=None`, it is also passed through to recursive calls as None. Its default value of `[]` avoids
        excessive recursion from the top-level call, by allowing things to be added to the exclusion list for
        recursive calls.

        :param recurse: include all transitive dependents, not just those that immediately depend on the module.
        """
        dependents = self.module_dependents.get(module_name, [])
        if recurse:
            # Fetch the dependents of each of the dependents of this module
            # This should never result in an infinite loop, since we check for cycles in the graph
            # If the check hasn't been run, things might go bad!
            for dep_mod in dependents:
                if exclude is not None:
                    # Don't recurse if module is in the exclude list
                    if dep_mod in exclude:
                        continue
                    else:
                        rec_exclude = list(set(exclude + dependents))
                else:
                    rec_exclude = None

                dependents.extend(self.get_dependent_modules(dep_mod, recurse=True, exclude=rec_exclude))
        return remove_duplicates(dependents)

    def append_module(self, module_info):
        """
        Add a moduleinfo to the end of the pipeline. This is mainly for use while loaded a pipeline from a
        config file.

        """
        from pimlico.core.modules.multistage import MultistageModuleInfo

        if isinstance(module_info, MultistageModuleInfo):
            # For multistage modules, add each their internal modules (stages)
            # Also make the main module available in the module info dict, but not in the module order
            for int_mod in module_info.internal_modules:
                self.append_module(int_mod)
        else:
            self.module_order.append(module_info.module_name)

        self.module_infos[module_info.module_name] = module_info
        # Check that the moduleinfo knows what pipeline it's in (it's usually already set by this point)
        module_info.pipeline = self
        # Keep a dictionary of expanded modules
        if module_info.alt_expanded_from is not None:
            self.expanded_modules.setdefault(module_info.alt_expanded_from, []).append(module_info.module_name)

    def get_module_schedule(self):
        """
        Work out the order in which modules should be executed. This is an ordering that respects
        dependencies, so that modules are executed after their dependencies, but otherwise follows the
        order in which modules were specified in the config.

        :return: list of module names
        """
        module_schedule = list(self.module_order)
        # Go through modules, looking for ordering constraints
        for module_name in self.modules:
            module = self[module_name]

            if not module.module_executable:
                # This module doesn't need to be executed: leave out
                module_schedule.remove(module_name)
            else:
                for dep_module_name in module.dependencies:
                    # Module dependency must be executed first
                    if dep_module_name in module_schedule and \
                                    module_schedule.index(module_name) < module_schedule.index(dep_module_name):
                        # These are in the wrong order
                        # Move dependency to just before dependent module
                        module_schedule.remove(dep_module_name)
                        module_schedule.insert(module_schedule.index(module_name), dep_module_name)
        # Provided there are no cycling dependencies, this ordering now respects the dependencies
        return module_schedule

    def reset_all_modules(self):
        """
        Resets the execution states of all modules, restoring the output dirs as if nothing's been run.

        """
        for module_name in self.modules:
            self[module_name].reset_execution()

    def path_relative_to_config(self, path):
        """
        Get an absolute path to a file/directory that's been specified relative to a config
        file (usually within the config file).

        :param path: relative path
        :return: absolute path
        """
        config_dir = os.path.dirname(os.path.abspath(self.filename))
        return os.path.abspath(os.path.join(config_dir, path))

    @property
    def short_term_store(self):
        """ For backwards compatibility: returns output path """
        warnings.warn("Used deprecated attribute 'short_term_store'. Should use new named storage location system. "
                      "(Perhaps 'pipeline.output_path' is appropriate?)", stacklevel=2)
        return self.output_path

    @property
    def long_term_store(self):
        """ For backwards compatibility: return storage location 'long' if it exists, else first storage location """
        warnings.warn("Used deprecated attribute 'long_term_store'. Should use new named storage location system")
        return self.named_storage_locations.get("long", self.storage_locations[0][1])

    @property
    def named_storage_locations(self):
        return dict(self.storage_locations)

    @property
    def store_names(self):
        return [n for (n, loc) in self.storage_locations]

    @property
    def output_path(self):
        return self.named_storage_locations[self.output_store]

    @staticmethod
    def load(filename, local_config=None, variant="main", override_local_config={}, only_override_config=False):
        """
        Main function that loads a pipeline from a config file.

        :param filename: file to read config from
        :param local_config: location of local config file, where we'll read system-wide config.
            Usually not specified, in which case standard locations are
            searched. When loading programmatically, you might want to give this
        :param variant: pipeline variant to load
        :param override_local_config: extra configuration values to override the system-wide config
        :param only_override_config: don't load local config from files, just use that given in override_local_config.
            Used for loading test pipelines
        :return:
        """
        from pimlico.core.modules.base import ModuleInfoLoadError
        from pimlico.core.modules.base import load_module_info
        from pimlico.core.modules.inputs import input_module_factory
        from pimlico.core.modules.map import DocumentMapModuleInfo
        from pimlico.core.modules.map.filter import wrap_module_info_as_filter
        from pimlico.core.modules.options import str_to_bool, ModuleOptionParseError

        if variant is None:
            variant = "main"

        local_config_data, used_config_sources = \
            PipelineConfig.load_local_config(filename=local_config, override=override_local_config,
                                             only_override=only_override_config)

        # Special vars are available for substitution in all options, including other vars
        special_vars = {
            "project_root": PROJECT_ROOT,
            "pimlico_root": PIMLICO_ROOT,
            "output_dir": OUTPUT_DIR,
            "home": os.path.expanduser("~"),
            "test_data_dir": TEST_DATA_DIR,
        }

        # Perform pre-processing of config file to replace includes, etc
        config_sections, available_variants, vars, all_filenames, section_docstrings = \
            preprocess_config_file(os.path.abspath(filename), variant=variant, initial_vars=special_vars)
        # If we were asked to load a particular variant, check it's in the list of available variants
        if variant != "main" and variant not in available_variants:
            raise PipelineConfigParseError("could not load pipeline variant '%s': it is not declared anywhere in the "
                                           "config file" % variant)
        config_section_dict = dict(config_sections)

        # Check for the special overall pipeline config section "pipeline"
        if "pipeline" not in config_section_dict:
            raise PipelineConfigParseError("no 'pipeline' section found in config: must be supplied to give basic "
                                           "pipeline configuration")
        # Include special variables in those used for substitutions
        vars.update(special_vars)
        # Do variable interpolation in the pipeline config section as well as module configs
        pipeline_config = dict([
            (key, var_substitute(val, vars)) for (key, val) in config_section_dict["pipeline"].items()
        ])

        # Deal with the special "alias" modules, which are not separate module, but just define new names
        aliases = {}
        for section, section_config in config_sections:
            if section_config.get("type", None) == "alias":
                if "input" not in section_config:
                    raise PipelineConfigParseError("module alias '%s' must have an 'input' option specifying which "
                                                   "module it is an alias for" % section)
                aliases[section] = section_config["input"]
                # Later, we'll check that the module referred to exists
        # Remove the aliases from the config sections, as we don't need to process them any more
        config_sections = [
            (section, section_config) for section, section_config in config_sections if section not in aliases
        ]
        module_order = [section for section, config in config_sections if section != "pipeline"]

        # All other sections of the config describe a module instance
        # Options will be further processed as the module infos are loaded
        raw_module_options = OrderedDict(
            (
                section,
                # Perform our own version of interpolation here, substituting values from the vars section into others
                dict((key, var_substitute(val, vars)) for (key, val) in config_section_dict[section].items())
            ) for section in module_order
        )

        # Check that we have a module for every alias
        for alias, alias_target in aliases.items():
            if alias_target not in raw_module_options:
                raise PipelineStructureError("alias '%s' specified for undefined module '%s'" % (alias, alias_target))

        # Process configs to get out the core things we need
        if "name" not in pipeline_config:
            raise PipelineConfigParseError("pipeline name must be specified as 'name' attribute in pipeline section")
        name = pipeline_config["name"]

        # Check that this pipeline is compatible with the Pimlico version being used
        if "release" not in pipeline_config:
            raise PipelineConfigParseError("Pimlico release version must be specified as 'release' attribute in "
                                           "pipeline section")
        if pipeline_config["release"] == "latest":
            # Allow for a special case of the value "latest"
            # Not good practice to use this in real pipelines, but handy for tests, where we always want to be using the
            #  latest release
            from pimlico import __version__
            pipeline_config["release"] = __version__
        check_release(pipeline_config["release"])

        # Some modules need to know which of their (potential) outputs get used by other models when they're loaded
        # We load modules in the order they're specified, so that we know we've loaded all the dependencies,
        # but this means we've not yet loaded the modules that use a module's outputs
        # Build a list of used outputs, before loading any modules
        used_outputs = {}
        for module_name in module_order:
            # Do minimal processing to get input connections: more thorough checks are done during instantiation
            for opt_name, opt_value in raw_module_options[module_name].items():
                if opt_name == "input" or opt_name.startswith("input_"):
                    if "." in opt_value:
                        # Module name + output name
                        input_module, __, input_module_output = opt_value.partition(".")
                    else:
                        # Module name, with default output
                        input_module = opt_value
                        input_module_output = None
                    used_outputs.setdefault(input_module, set([])).add(input_module_output)

        # Prepare a PipelineConfig instance that we'll add moduleinfos to
        pipeline = PipelineConfig(
            name, pipeline_config, local_config_data,
            filename=filename, variant=variant, available_variants=list(sorted(available_variants)),
            all_filenames=all_filenames, module_aliases=aliases, local_config_sources=used_config_sources,
        )

        # Now we're ready to try loading each of the module infos in turn
        module_infos = {}
        loaded_modules = []
        # Construct a mapping from the section names as written to expanded sections and the other way
        original_to_expanded_sections = {}
        expanded_to_original_sections = {}
        expanded_sections = {}  # This one stores None for non-expanded sections, or the original name if expanded
        expanded_param_settings = {}  # And the settings used in the expansions

        for module_name in module_order:
            try:
                module_config = raw_module_options[module_name]

                # Work out what the previous module was, so that we can use it as a default connection
                previous_module_name = loaded_modules[-1] if len(loaded_modules) else None

                # Load the module info class for the declared type of the module in the config
                module_type_name = module_config.pop("type", None)
                if module_type_name is None:
                    raise PipelineConfigParseError("module %s does not specify a type" % module_name)
                try:
                    # First see if this is a datatype
                    # If so, all options other than 'dir' and other special keys are used as datatype options
                    datatype_options = OrderedDict((k, v) for (k, v) in module_config.items()
                                                   if k not in ["dir", "tie_alts", "alt_naming"]
                                                   and not k.startswith("modvar_"))
                    datatype_class = load_datatype(module_type_name, options=datatype_options)
                    # Params used as datatype options should be removed from config
                    for key in datatype_options:
                        del module_config[key]
                except DatatypeLoadError:
                    # Not a datatype
                    try:
                        module_info_class = load_module_info(module_type_name)
                    except ModuleInfoLoadError as e:
                        raise PipelineConfigParseError("could not load a module type for the name '{}': "
                                                       "no datatype or module type could be loaded".format(module_type_name))
                else:
                    # Get an input module info class for this datatype
                    module_info_class = input_module_factory(datatype_class)

                # Fill in default inputs where they've been left unspecified
                if len(module_info_class.module_inputs) == 1:
                    # Single input may be given without specifying name
                    input_name = "input_%s" % module_info_class.module_inputs[0][0]
                    if "input" not in module_config and input_name not in module_config:
                        missing_inputs = [input_name]
                    else:
                        missing_inputs = []
                else:
                    required_inputs = ["input_%s" % input_name
                                       for (input_name, __) in module_info_class.module_inputs]
                    missing_inputs = [name for name in required_inputs if name not in module_config]

                for input_key in missing_inputs:
                    # Supply the previous module in the config file as default for missing inputs
                    if previous_module_name is None:
                        raise PipelineStructureError("module '%s' has no input specified, but there's no previous "
                                                     "module to use as default" % module_name)
                    else:
                        # By default, connect to the default output from the previous module
                        module_config[input_key] = previous_module_name

                ############## Special parameters ####################
                # Various types of special parameters, which apply to all module types, are processed here
                # And removed from the config so that they're not passed through to the ModuleInfo constructor

                # Allow document map types to be used as filters simply by specifying filter=T
                filter_type = str_to_bool(module_config.pop("filter", ""))

                # Check for the tie_alts option, which causes us to tie together lists of alternatives instead
                # of taking their product
                tie_alts_raw = module_config.pop("tie_alts", "")
                if not isinstance(tie_alts_raw, basestring) or \
                        tie_alts_raw.lower() in ["", "0", "f", "false", "n", "no"]:
                    # Don't tie anything: multiply out all alternatives
                    tie_alts = []
                elif tie_alts_raw.lower() in ["1", "t", "true", "y", "yes"]:
                    # Tie all alternatives together
                    tie_alts = "all"
                else:
                    # Otherwise, must be a specification of groups of params with alternatives that will be tied
                    # Each group is separated by spaces
                    # Each param name within a group is separated by |s
                    tie_alts = [group.split("|") for group in tie_alts_raw.split(" ")]

                # Module variable parameters
                modvar_params = [(key, val) for (key, val) in module_config.items() if key.startswith("modvar_")]
                for modvar_key, modvar_val in modvar_params:
                    module_config.pop(modvar_key)
                modvar_params = [(key[7:], val) for (key, val) in modvar_params]
                # Don't do any more processing of these yet, but come back to them once we've expanded alts

                # Remove the alt_naming parameter now, which we use later on
                alt_naming = module_config.pop("alt_naming", "")

                # End of special parameter processing
                #########################################################

                # Parameters and inputs can be given multiple values, separated by |s
                # In this case, we need to multiply out all the alternatives, to make multiple modules
                # Check whether any of the inputs to this module come from a previous module that's been expanded into
                # multiple. If so, give this model alternative inputs to cover them all.
                # At this stage, any expanded modules specified with the *name notation (input to a MultipleInputs)
                # will not be picked up, as they've still got the * on them
                for input_opt in [key for key in module_config.keys() if key == "input" or key.startswith("input_")]:
                    # Check for a list of alt names within []s
                    # This should be expanded into a list of modules names, each with a different alt name
                    # E.g. mymod[alt1,alt2,alt3] -> mymod[alt1],mymod[alt2],mymod[alt3]
                    module_config[input_opt] = _expand_alt_names_list(module_config[input_opt])

                    new_alternatives = []
                    # It's possible for the value to already have alternatives, in which case we include them all
                    for original_val in module_config[input_opt].split("|"):
                        # If there's a list of values here, we need to handle it carefully
                        new_items = []
                        new_item_alt_names = []
                        for original_val_item in original_val.split(","):
                            original_val_item = original_val_item.strip()
                            # If the input connection has more than just a module name, we only modify the module name
                            val_module_name, __, rest_of_val = original_val_item.partition(".")
                            # If module name is unknown, this will be a problem, but leave the error handling till later
                            # For safety's sake, skip over anything that starts with *
                            if len(original_to_expanded_sections.get(val_module_name, [])) > 1 and \
                                    not val_module_name.startswith("*"):
                                # The previous module has been expanded: add all of the resulting modules as alternatives
                                previous_modules = original_to_expanded_sections[val_module_name]
                                # Include the rest of the input specifier (generally an output name)
                                previous_modules = [
                                    "%s.%s" % (mod, rest_of_val) if rest_of_val else mod for mod in previous_modules
                                ]
                                # If the previous module names are already in the form module[alt_name], take the alt_name
                                # from there
                                previous_module_alt_names = [
                                    mod[mod.index("[")+1:mod.index("]")] if "[" in mod else None for mod in previous_modules
                                ]
                                new_items.append(previous_modules)
                                # The different items might give us different alt names
                                # In that case, we'll just use the first for every alt
                                new_item_alt_names.append(previous_module_alt_names)
                            else:
                                # Previous module this one takes input from has not been expanded: leave unchanged
                                # Or it starts with * or includes a ,
                                new_items.append([original_val_item])
                                # No alternative name associated with this (unless it's already given)
                                new_item_alt_names.append([None])
                        if len(new_items) == 1:
                            # Simplest case: no comma-separated list at all
                            new_alternatives.extend(new_items[0])
                        elif any(len(i) == 1 for i in new_items) and not all(len(i) == 1 for i in new_items):
                            # Some items have only one alternative, but others have more
                            num_alts = next((len(i) for i in new_items if len(i) > 1))
                            # Multiply the ones that have only one alternative, to use that same value for each of the
                            #  other items
                            new_items = [i if len(i) > 1 else i*num_alts for i in new_items]
                            # Now zip together the alternative values for each list item
                            new_alternatives = [",".join(item_alts) for item_alts in zip(*new_items)]
                        elif any(len(i) != len(new_items[0]) for i in new_items[1:]):
                            # Otherwise, we expect each item in the list to have ended up with the same number
                            #  of alternatives, so we can zip them together
                            raise PipelineConfigParseError(
                                "error processing alternative values for {} to {}. When expanding a list of module "
                                "names, every item in the list must have the same number of alternatives, or just "
                                "one alternative. Got alternative numbers '{}' from list '{}'".format(
                                    input_opt, module_name, ", ".join(str(len(i)) for i in new_items), original_val
                                ))
                        else:
                            # All items have same number of alternatives
                            # Zip together the alternative values for each list item
                            new_alternatives = [",".join(item_alts) for item_alts in zip(*new_items)]

                        new_alts_with_names = []
                        for alt_num, new_alt in enumerate(new_alternatives):
                            if new_alt.startswith("{"):
                                # This already has an alternative name: don't do anything
                                new_alts_with_names.append(new_alt)
                            else:
                                # Try to find a name from one of the items in the list
                                try:
                                    new_name = next((item_alt_names[alt_num]
                                                for item_alt_names in new_item_alt_names
                                                if len(item_alt_names) > alt_num
                                                and item_alt_names[alt_num] is not None))
                                except StopIteration:
                                    # No name found: just leave the value as it is, unnamed
                                    new_alts_with_names.append(new_alt)
                                else:
                                    new_alts_with_names.append("{%s}%s" % (new_name, new_alt))
                        new_alternatives = new_alts_with_names
                    module_config[input_opt] = "|".join(new_alternatives)

                # Now look for any options with alternative values and expand them out into multiple module configs
                expanded_module_configs = []
                if any("|" in val for val in module_config.values()):
                    # There are alternatives in this module: expand into multiple modules
                    # Important to use an ordered dict, so that the parameters are kept in their original order
                    params_with_alternatives = OrderedDict()
                    alternative_names = {}
                    fixed_params = OrderedDict()
                    for key, val in module_config.items():
                        if "|" in val:
                            # Split up the alternatives and allow space around the |s
                            alts = [alt.strip() for alt in val.split("|")]
                            # The alternatives may provide names to identify them by, rather than the param val itself
                            # Get rid of these from the param vals
                            param_vals = [
                                (alt.partition("}")[2].strip(), alt[1:alt.index("}")]) if alt.startswith("{")  # Use given name
                                else (alt, alt)  # Use param itself as name
                                for alt in alts
                            ]
                            params_with_alternatives[key] = param_vals
                            # Also pull out the names so we can use them
                            alternative_names[key] = [alt[1:alt.index("}")] if alt.startswith("{") else alt for alt in alts]
                        else:
                            fixed_params[key] = val

                    if len(params_with_alternatives) > 0:
                        if tie_alts == "all":
                            # Tie all params with alternatives together
                            # Simply put them all in one group and multiply_alternatives will tie them
                            param_alt_groups = [list(params_with_alternatives.items())]
                        else:
                            # First check that all the params that have been named in tying groups exist and have
                            #  alternatives
                            for param_name in sum(tie_alts, []):
                                if param_name not in params_with_alternatives:
                                    if param_name in fixed_params:
                                        raise PipelineStructureError(
                                            "parameter '%s' was specified in tie_alts for module '%s', "
                                            "but doesn't have any alternative values" % (param_name, module_name)
                                        )
                                    else:
                                        # Not even a specified parameter name
                                        raise PipelineStructureError(
                                            "parameter '%s' was specified in tie_alts for module '%s', but isn't "
                                            "given as one of the module's parameters" % (param_name, module_name)
                                        )
                            # Generate all combinations of params that have alternatives, tying some if requested
                            tied_group_dict = {}
                            untied_groups = []
                            for param_name, param_vals in params_with_alternatives.items():
                                # See whether this param name is being tied
                                try:
                                    group_num = next((
                                        i for i, param_set in enumerate(tie_alts) if param_name in param_set))
                                except StopIteration:
                                    # No in a tied group: just add it to its own group (i.e. don't tie)
                                    untied_groups.append([(param_name, param_vals)])
                                else:
                                    tied_group_dict.setdefault(group_num, []).append((param_name, param_vals))
                            param_alt_groups = list(tied_group_dict.values()) + untied_groups
                        try:
                            alternative_configs = multiply_alternatives(param_alt_groups)
                        except ParameterTyingError as e:
                            raise PipelineStructureError("could not tie parameters to %s: %s" % (module_name, e))
                    else:
                        alternative_configs = [[]]

                    # Also allow the specification of various options to do with how expanded alternatives are named
                    alt_name_inputname = False
                    alt_name_from_options = None
                    if alt_naming == "":
                        # Default naming scheme: fully specify param=val (with some abbreviations)
                        pos_alt_names = False
                    elif alt_naming.startswith("full"):
                        # Explicit full naming scheme: same as default, but allows extra options
                        pos_alt_names = False
                        extra_opts = alt_naming[4:].strip("()").split(",")
                        for extra_opt in extra_opts:
                            if extra_opt == "inputname":
                                # Strip the "input_" from input names
                                alt_name_inputname = True
                            # Can add more here in future
                            else:
                                raise PipelineStructureError("unknown alternative naming option '%s'" % extra_opt)
                    elif alt_naming == "pos":
                        # Positional naming
                        pos_alt_names = True
                    elif alt_naming.startswith("option"):
                        # Take the names just from the alt names on a particular option
                        # In many cases, this will lead to clashes, but not always: for example, if tying alts
                        alt_name_from_options = [x.strip() for x in alt_naming[6:].strip("()").split(",")]
                    else:
                        raise PipelineConfigParseError("could not interpret alt_naming option to %s: %s" %
                                                       (module_name, alt_naming))

                    def _all_same(lst):
                        lst = [x for x in lst if x is not None]
                        if len(lst) < 2:
                            return True
                        else:
                            return all(x == lst[0] for x in lst[1:])

                    _key_name = lambda x: x
                    if alt_name_inputname:
                        # For inputs, just give the input name, not "input_<inputname>"
                        # This can lead to param name clashing, which is why it has to be selected by the user
                        _key_name = lambda x: x[6:] if x.startswith("input_") else x

                    def _param_set_to_name(params_set):
                        # Here we allow for several different behaviours, depending on options
                        if alt_name_from_options is not None:
                            alt_name_parts = []
                            for alt_name_source in alt_name_from_options:
                                try:
                                    val, name = dict(params_set)[alt_name_source]
                                except KeyError:
                                    raise PipelineConfigParseError("tried to take alt name from option '%s' for module %s, "
                                                                   "but that option either doesn't exist or doesn't have "
                                                                   "alternative values" % (alt_name_source, module_name))
                                alt_name_parts.append(name)
                            return "~".join(alt_name_parts)
                        elif pos_alt_names:
                            # No param names, just positional value names
                            # In this case, don't abbreviate where names are all the same, as it's confusing
                            return "~".join(name for (key, (val, name)) in params_set if name is not None)
                        elif len(params_set) == 1 or _all_same(name for (key, (val, name)) in params_set):
                            # If there's only 1 parameter that's varied, don't include the key in the name
                            # If a special name was given, use it; otherwise, this is just the param value
                            # If all the params' values happen to have the same name, just use that
                            # (This is common, if they've come from the same alternatives earlier in the pipeline
                            return params_set[0][1][1]
                        else:
                            return "~".join(
                                "%s=%s" % (_key_name(key), name)
                                for (key, (val, name)) in params_set if name is not None
                            )

                    # Generate a name for each
                    module_alt_names = [_param_set_to_name(params_set) for params_set in alternative_configs]
                    # Check that the names are valid alt names
                    for n in module_alt_names:
                        try:
                            _check_valid_alt_name(n)
                        except ValueError as e:
                            raise PipelineConfigParseError("invalid alt name for module {}: {}".format(module_name, e))
                    alternative_config_names = [
                        "%s[%s]" % (module_name, alt_name) for alt_name in module_alt_names
                    ]
                    for exp_name, params_set in zip(alternative_config_names, alternative_configs):
                        expanded_param_settings[exp_name] = params_set

                    # Add in fixed params to them all
                    alternative_configs = [
                        dict([(key, val) for (key, (val, name)) in params_set], **copy.deepcopy(fixed_params))
                        for params_set in alternative_configs
                    ]
                    expanded_module_configs.extend(zip(alternative_config_names, alternative_configs))
                    # Keep a record of what expansions we've done
                    original_to_expanded_sections[module_name] = alternative_config_names
                    for exp_name in alternative_config_names:
                        expanded_to_original_sections[exp_name] = module_name
                        expanded_sections[exp_name] = module_name

                    # We also need to do this for any aliases to this module
                    aliases_to_expand = [alias for (alias, trg) in aliases.items() if trg == module_name]
                    for alias in aliases_to_expand:
                        del aliases[alias]
                        for alt_name in module_alt_names:
                            exp_alias = "%s[%s]" % (alias, alt_name)
                            exp_module = "%s[%s]" % (module_name, alt_name)
                            aliases[exp_alias] = exp_module

                            # Keep a record of what expansions we've done
                            original_to_expanded_sections.setdefault(alias, []).append(exp_alias)
                            expanded_to_original_sections[exp_alias] = alias
                            expanded_sections[exp_alias] = alias
                else:
                    # No alternatives
                    expanded_module_configs.append((module_name, module_config))
                    original_to_expanded_sections[module_name] = [module_name]
                    expanded_to_original_sections[module_name] = module_name
                    expanded_sections[module_name] = None
                    expanded_param_settings[module_name] = []

                # Now we create a module info for every expanded module config
                # Often this will just be one, but it could be many, if there are several options with alternatives
                for expanded_module_name, expanded_module_config in expanded_module_configs:
                    # Pass in all other options to the info constructor
                    options_dict = dict(expanded_module_config)

                    try:
                        # Pull out the output option if it's there, to specify optional outputs
                        output_opt = options_dict.pop("output", "")
                        outputs = output_opt.split(",") if output_opt else []
                        # Pull out the input options and match them up with inputs
                        inputs = module_info_class.extract_input_options(
                            options_dict, module_name=module_name, previous_module_name=previous_module_name,
                            module_expansions=original_to_expanded_sections
                        )
                    except ModuleOptionParseError as e:
                        raise PipelineConfigParseError("error in '%s' options: %s" % (module_name, e))

                    # Now, before processing all the module parameters, perform any module variable substitution
                    # on the raw strings

                    # Check that all the modules that feed into this one's inputs have been defined already
                    input_module_names = []
                    modvar_dependent_inputs = []
                    for input_name, input_specs in inputs.items():
                        input_module_group = []
                        for input_spec_num, input_spec in enumerate(input_specs):
                            if "$(" in input_spec[0] or "$(" in input_spec[2]:
                                # Input module names are allowed to be dependent on module variables, but if they
                                # are we can't inherit modvars from their input modules (cart before horse).
                                # We leave them out here and come back and fill in the modvar later
                                modvar_dependent_inputs.append((input_name, input_spec_num))
                            elif input_spec[0] not in pipeline:
                                raise PipelineStructureError("unknown module '%s' in inputs to '%s'" %
                                                             (input_spec[0], expanded_module_name))
                            else:
                                # Note all the modules that provide input to this one
                                input_module_group.append(input_spec[0])
                        input_module_names.append((input_name, input_module_group))
                    input_modules = [
                        (group_name, [pipeline[mod_name] for mod_name in img])
                        for (group_name, img) in input_module_names
                    ]

                    # Update the module variables on the basis of any assignments made in the parameters
                    module_variables, inherited_variables = \
                        update_module_variables(input_modules, modvar_params,
                                                expanded_param_settings[expanded_module_name])

                    # Allow modvar values to be substituted into module parameters
                    substitute_modvars(
                        options_dict, module_variables, expanded_param_settings[expanded_module_name],
                        inherited_variables
                    )
                    # Allow modvar values also to be used in input names (which were held out when inheriting modvars)
                    add_after = {}
                    for input_name, input_spec_num in modvar_dependent_inputs:
                        # Doing modvar substitution can result in a single value (input source) being expanded out
                        # into multiple, by a modvar evaluating to a list
                        new_input_names = substitute_modvars_in_value(
                            input_name, inputs[input_name][input_spec_num][0], module_variables,
                            expanded_param_settings[expanded_module_name], inherited_variables,
                            list_action="expand"
                        )
                        new_input_multiplier = substitute_modvars_in_value(
                            input_name, inputs[input_name][input_spec_num][2], module_variables,
                            expanded_param_settings[expanded_module_name], inherited_variables,
                            list_action="error"
                        )
                        if type(new_input_names) is not list:
                            new_input_names = [new_input_names]
                        new_input_specs = [
                            tuple([iname] + [inputs[input_name][input_spec_num][1]] + [new_input_multiplier])
                            for iname in new_input_names
                        ]
                        # In the simple and most common case that there's only one resulting input spec, just use that
                        inputs[input_name][input_spec_num] = new_input_specs[0]
                        if len(new_input_specs) > 1:
                            # If there are multiple, we need to come back and add the rest at the end, so as not to
                            # spoil the item numbering
                            add_after.setdefault(input_name, []).append((input_spec_num, new_input_specs[1:]))
                    # Go back and fill in the extra input specs we need
                    for input_name, to_add in add_after.items():
                        added = 0
                        for original_spec_num, new_specs in to_add:
                            for offset, new_spec in enumerate(new_specs):
                                inputs[input_name].insert(original_spec_num + 1 + offset + added, new_spec)
                            added += len(new_specs)

                    # Apply input multipliers
                    for input_name, input_specs in inputs.items():
                        new_input_specs = []
                        for _mod, _output, _mlt in input_specs:
                            _mlt = _mlt.strip(" ()")
                            if len(_mlt) == 0:
                                # Most common case: no multiplier at all
                                _mlt = 1
                            else:
                                try:
                                    _mlt = int(_mlt)
                                except ValueError:
                                    raise PipelineConfigParseError("input multiplier must be an integer value after "
                                                                   "variable expansion. Got '{}' in input '{}' to "
                                                                   "module '{}'".format(_mlt, input_name, module_name))
                            new_input_specs.extend([(_mod, _output)] * _mlt)
                        inputs[input_name] = new_input_specs

                    # Replace input specs of form module_name.* with all the (non-optional) outputs from module_name
                    inputs = dict(
                        (input_name, sum([
                            # Replace * outputs with a list of the same module with each of the outputs
                            [(_mod, output_name) for (output_name,__) in pipeline[_mod].available_outputs]
                                if _output == "*"
                            # Other module/output pairs are left
                            else [(_mod, _output)]
                            for _mod, _output in input_specs
                        ], []))
                        for input_name, input_specs in inputs.items()
                    )

                    inputs = dict(
                        (input_name, [spec[:2] for spec in input_spec]) for (input_name, input_spec) in inputs.items()
                    )

                    # We're now ready to do the main parameter processing, which is dependent on the module
                    options = module_info_class.process_module_options(options_dict)

                    # Get additional outputs to be included on the basis of the options, according to module
                    # type's own logic
                    optional_outputs = set(outputs) | \
                                       set(module_info_class.get_extra_outputs_from_options(options_dict, inputs))

                    # Instantiate the module info
                    module_info = module_info_class(
                        expanded_module_name, pipeline, inputs=inputs, options=options,
                        optional_outputs=optional_outputs, docstring=section_docstrings.get(module_name, ""),
                        # Make sure that the module info includes any optional outputs that are used by other modules
                        include_outputs=used_outputs.get(module_name, []),
                        # Store the name of the module this was expanded from
                        alt_expanded_from=expanded_sections[expanded_module_name],
                        # Also store the parameter settings that this alternative used
                        alt_param_settings=expanded_param_settings[expanded_module_name],
                        module_variables=module_variables,
                    )

                    # If we're loading as a filter, wrap the module info
                    if filter_type:
                        if not issubclass(module_info_class, DocumentMapModuleInfo):
                            raise PipelineStructureError(
                                "only document map module types can be treated as filters. Got option filter=True for "
                                "module %s" % module_name
                            )
                        module_info = wrap_module_info_as_filter(module_info)

                    # Add to the end of the pipeline
                    pipeline.append_module(module_info)

                    module_infos[expanded_module_name] = module_info
                    loaded_modules.append(module_name)
            except ModuleInfoLoadError as e:
                raise PipelineConfigParseError("error loading module metadata for module '%s': %s" % (module_name, e))

        try:
            # Run all type-checking straight away so we know this is a valid pipeline
            check_pipeline(pipeline)
        except PipelineCheckError as e:
            raise PipelineConfigParseError("failed checks: %s" % e, cause=e, explanation=e.explanation)

        return pipeline

    @staticmethod
    def load_local_config(filename=None, override={}, only_override=False):
        """
        Load local config parameters. These are usually specified in a `.pimlico` file, but may be overridden by
        other config locations, on the command line, or elsewhere programmatically.

        If only_override=True, don't load any files, just use the values given in override. The various
        locations for local config files will not be checked (which usually happens when filename=None).
        This is not useful for normal pipeline loading, but is used for loading test pipelines.

        """
        # Keep a record of where we got config from, for debugging purposes
        used_config_sources = []

        if only_override:
            local_config_data = OrderedDict()
        else:
            if filename is None:
                home_dir = os.path.expanduser("~")
                # Use the default locations for local config file
                local_config = []
                # First, look for the basic config
                # If other config files are found below, we don't complain about this not existing,
                # but usually it must exist: we will complain below if nothing else is found
                basic_config_filename = os.path.join(home_dir, ".pimlico")
                if os.path.exists(basic_config_filename):
                    local_config.append(basic_config_filename)

                # Allow other files to override the settings in this basic one
                # Look for any files matching the pattern .pimlico_*
                alt_config_files = [f for f in os.listdir(home_dir) if f.startswith(".pimlico_")]

                # You may specify config files for specific hosts
                hostname = gethostname()
                if hostname is not None and len(hostname) > 0:
                    for alt_config_filename in alt_config_files:
                        suffix = alt_config_filename[9:]
                        if hostname == suffix:
                            # Our hostname matches a hostname-specific config file .pimlico_<hostname>
                            local_config.append(os.path.join(home_dir, alt_config_filename))
                            # Only allow one host-specific config file
                            break
                        elif suffix.endswith("-") and hostname.startswith(suffix[:-1]):
                            # Hostname match hostname-prefix-specific config file .pimlico_<hostname_prefix>-
                            local_config.append(os.path.join(home_dir, alt_config_filename))
                            break
                            
                if len(local_config) == 0:
                    raise PipelineConfigParseError("basic Pimlico local config file does not exist and no other local "
                                                   "config files are available in the current context. Looked for "
                                                   "basic config in {}".format(basic_config_filename))
            else:
                local_config = [filename]

            def _load_config_file(fn):
                # Read in the local config and supply a section heading to satisfy config parser
                with open(fn, "r") as f:
                    local_text_buffer = "[main]\n%s" % f.read()
                # User config parser to interpret file contents
                local_config_parser = ConfigParser()
                local_config_parser.read_string(local_text_buffer)
                # Get a dictionary of settings from the file
                return OrderedDict(local_config_parser.items("main"))

            local_config_data = OrderedDict()
            # Process each file, loading config data from it
            for local_config_filename in local_config:
                local_config_file_data = _load_config_file(local_config_filename)
                if local_config_file_data:
                    # Override previous local config data
                    local_config_data.update(local_config_file_data)
                    # Mark this source as used (for debugging)
                    used_config_sources.append("file %s" % local_config_filename)

        if override:
            # Allow parameters to be overridden on the command line
            local_config_data.update(override)
            used_config_sources.append("command-line overrides")

        # We used to require "short_term_store" and "long_term_store"
        # This has now been replaced by the more flexible storage system that allows unlimited locations
        # For backwards compatibility, we convert these values as we load them and warn the user
        if "short_term_store" in local_config_data or "long_term_store" in local_config_data:
            warnings.warn("Local config used deprecated 'short_term_store'/'long_term_store' parameters. "
                          "Converting to new named storage system. You should update your local config. "
                          "See https://bit.ly/2mcvZhT")
        if "short_term_store" in local_config_data:
            # This was the default output location, so we should use the value as the first location, unless one
            # is already given
            if any(key.startswith("store") for key in local_config_data.keys()):
                local_config_data["storage_short"] = local_config_data["short_term_store"]
            else:
                # Insert the named storage location, ensuring it comes before any others
                local_config_data = OrderedDict(
                    [("store_short", local_config_data["short_term_store"])] +
                    list(local_config_data.items())
                )
            del local_config_data["short_term_store"]
        if "long_term_store" in local_config_data:
            local_config_data["store_long"] = local_config_data["long_term_store"]
            del local_config_data["long_term_store"]

        # Check we've got all the essentials from somewhere
        for attr in REQUIRED_LOCAL_CONFIG:
            if attr not in local_config_data:
                raise PipelineConfigParseError("required attribute '%s' is not specified in local config" % attr)

        # Check that there's at least one storage location given
        if not any(key.startswith("store") for key in local_config_data.keys()):
            raise PipelineConfigParseError("no storage location was found in local config. You should specify "
                                           "at least one, either as a default 'store' parameter, or a named storage "
                                           "location 'store_<name>'")

        return local_config_data, used_config_sources

    @staticmethod
    def empty(local_config=None, override_local_config={}, override_pipeline_config={}, only_override_config=False):
        """
        Used to programmatically create an empty pipeline. It will contain no modules, but provides a gateway to
        system info, etc and can be used in place of a real Pimlico pipeline.

        :param local_config: filename to load local config from. If not given, the default locations are searched
        :param override_local_config: manually override certain local config parameters. Dict of parameter values
        :param only_override_config: don't load any files, just use the values given in override. The various
            locations for local config files will not be checked (which usually happens when filename=None).
            This is not useful for normal pipeline loading, but is used for loading test pipelines.
        :return: the :class:`PipelineConfig` instance
        """
        from pimlico import __version__ as current_pimlico_version

        local_config_data, used_config_sources = \
            PipelineConfig.load_local_config(filename=local_config, override=override_local_config,
                                             only_override=only_override_config)
        name = "empty_pipeline"
        pipeline_config = {
            "name": name,
            "release": current_pimlico_version,
        }
        pipeline_config.update(override_pipeline_config)

        pipeline = PipelineConfig(
            name, pipeline_config, local_config_data,
            filename=None, variant="main", available_variants=[], all_filenames=[],
        )

        try:
            check_pipeline(pipeline)
        except PipelineCheckError as e:
            raise PipelineConfigParseError("empty pipeline created, but failed checks: %s" % e, cause=e)

        return pipeline

    def find_data_path(self, path, default=None):
        """
        Given a path to a data dir/file relative to a data store, tries taking it relative to various store base
        dirs. If it exists in a store, that absolute path is returned. If it exists in no store, return None.
        If the path is already an absolute path, nothing is done to it.

        Searches all the specified storage locations.

        :param path: path to data, relative to store base
        :param default: usually, return None if no data is found. If default is given, return the path
            relative to the named storage location if no data is found. Special value "output" returns path
            relative to output location, whichever of the storage locations that might be
        :return: absolute path to data, or None if not found in any store
        """
        return self.find_data(path, default=default)[1]

    def find_data_store(self, path, default=None):
        """
        Like `find_data_path()`, searches through storage locations to see if any of them
        include the data that lives at this relative path. This method returns the name of
        the store in which it was found.

        :param path: path to data, relative to store base
        :param default: usually, return None if no data is found. If default is given, return the path
            relative to the named storage location if no data is found. Special value "output" returns path
            relative to output location, whichever of the storage locations that might be
        :return: name of store
        """
        return self.find_data(path, default=default)[0]

    def find_data(self, path, default=None):
        """
        Given a path to a data dir/file relative to a data store, tries taking it relative to various store base
        dirs. If it exists in a store, that absolute path is returned. If it exists in no store, return None.
        If the path is already an absolute path, nothing is done to it.

        Searches all the specified storage locations.

        :param path: path to data, relative to store base
        :param default: usually, return None if no data is found. If default is given, return the path
            relative to the named storage location if no data is found. Special value "output" returns path
            relative to output location, whichever of the storage locations that might be
        :return: (store, path), where store is the name of the store used and path is
            absolute path to data, or None for both if not found in any store
        """
        if os.path.isabs(path):
            return None, path
        # Try all the possible locations for this relative path
        for store_name, abs_path in self.get_data_search_paths(path):
            if os.path.exists(abs_path):
                # Return the first path that exists
                return store_name, abs_path
        # The data was not found in any storage location
        if default == "output":
            # Return the path that would be used to output the data to
            return self.output_store, os.path.join(self.output_path, path)
        elif default is not None:
            # Return the path in a given default store
            return default, os.path.join(self.named_storage_locations[default], path)
        else:
            return None, None

    def get_data_search_paths(self, path):
        """
        Like `find_all_data_paths()`, but returns a list of all absolute paths which this data
        path could correspond to, whether or not they exist.

        :param path: relative path within Pimlico directory structures
        :return: list of string
        """
        return [(name, os.path.join(store_base, path)) for (name, store_base) in self.storage_locations]

    @property
    def step(self):
        return self._stepper is not None

    def enable_step(self):
        """
        Enable super-verbose, interactive step mode.

        ::seealso::

           Module :mod:pimlico.cli.debug
              The debug module defines the behaviour of step mode.

        """
        enable_step_for_pipeline(self)


def multiply_alternatives(alternative_params):
    """
    Input is a list of lists, representing groups of tied parameters.

    In the (default) untied case, each group contains a single parameter (along with its set of values).
    In the fully tied case (tie_alts=T), there's just one group containing all the parameters that
    have alternative values.

    """
    if len(alternative_params):
        # Take the first group of parameters
        param_group = alternative_params.pop()

        # Check that all params in the tied group have the same number of alternatives
        alt_nums = [len(alts) for (param_name, alts) in param_group]
        if not all(num == alt_nums[0] for num in alt_nums):
            raise ParameterTyingError(
                "parameters %s do not all have the same number of alternative values (%s): cannot tie them" % (
                    ", ".join(name for name, alts in param_group), ", ".join(str(num) for num in alt_nums)))

        # Expand the alternatives for the tied group together
        our_alternatives = [
            [(key, vals[i]) for (key, vals) in param_group] for i in range(alt_nums[0])
        ]
        # If all the params that are tied have the same names for corresponding values, we don't need to name
        # all of them. Instead, get a more concise module name by leaving our the names for all but one here,
        # so that we skip them when constructing the module name
        if all(
                (len(param_group) > 1 and
                    all(val_name is not None and val_name == param_group[0][1][1] for param_name, (val, val_name) in param_group))
                for param_group in our_alternatives):
            our_alternatives = [
                [param_group[0]] + [(key, (val, None)) for (key, (val, val_name)) in param_group[1:]]
                for param_group in our_alternatives
            ]
        # Recursively generate all alternatives by other keys
        sub_alternatives = multiply_alternatives(alternative_params)
        # Make a copy of each alternative combined with each val for this key
        return [alt_params + our_assignments for our_assignments in our_alternatives for alt_params in sub_alternatives]
    else:
        # No alternatives left, base case: return an empty list
        return [[]]


def update_module_variables(input_modules, modvar_params, expanded_params):
    """
    Given the ModuleInfo instances that provide input to a module and the parsed module variable update
    parameters (all those starting 'modvar_'), collect module variables from the inputs that this module
    should inherit and update them according to the parameters.

    :param input_modules: list of ModuleInfos that the module gets input from
    :param modvar_params: list of modvar params
    :return: module variables dict for the new module
    """
    # First go through the input modules to inherit all their mod vars
    module_variables = {}
    # Also keep track of what values we inherited from specific inputs
    inherited_variables = {}

    for input_name, module_group in input_modules:
        group_variables = {}
        for module in module_group:
            for var_name, var_val in module.module_variables.items():
                # If we get multiple values for the same module variable within a group (that is, on a multiple input
                #  to the same module input), we need to preserve them all, so we turn the modvar into a list
                if var_name in group_variables:
                    if type(group_variables[var_name]) is not list:
                        group_variables[var_name] = [group_variables[var_name]]
                    group_variables[var_name].append(var_val)
                else:
                    # Simply inherit the value
                    group_variables[var_name] = var_val
        # Name clashes not within the same group just get overwritten by later values
        module_variables.update(group_variables)
        inherited_variables[input_name] = group_variables

    # Apply all specified updates to the variables
    modvar_params_to_modvars(modvar_params, module_variables, expanded_params, inherited_variables)
    return module_variables, inherited_variables


def modvar_params_to_modvars(params, vars, expanded_params, variables_from_inputs):
    """
    Parse modvar_* params to work out what a module's module variables should be.

    """
    for key, val in params:
        # Preprocess to remove line breaks and surrounding space
        val = val.replace("\n", " ").strip()
        if val in ["none", "undefined"]:
            # Remove the variable
            del vars[key]
        else:
            try:
                vars[key], rest = _parse_modvar_param(val, vars, expanded_params, variables_from_inputs)
                rest = rest.strip()
                while rest.startswith(","):
                    new_val, rest = _parse_modvar_param(rest[1:], vars, expanded_params, variables_from_inputs)
                    if not isinstance(new_val, list):
                        new_val = [new_val]
                    if isinstance(vars[key], list):
                        vars[key].extend(new_val)
                    else:
                        vars[key] = [vars[key]] + new_val
                    rest = rest.strip()

                # After we've parsed everything we can, nothing else is allowed
                if len(rest.strip()):
                    raise ValueError("unexpected string: %s" % rest.strip())
            except ValueError as e:
                raise PipelineConfigParseError("could not parse module variable '%s = %s': %s" % (key, val, e))


var_name_re = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)?')
int_literal_re = re.compile(r'^\d+')


def _parse_modvar_param(param, vars, expanded_params, variables_from_inputs):
    if param.startswith('"'):
        # Start of a quoted string
        # Look for the next quote
        if '"' not in param[1:]:
            raise ValueError("unmatched quote at '%s'" % param[:10])
        val, __, rest = param[1:].partition('"')
    elif param.startswith("altname("):
        # Take the value of the alt name for a given parameter
        inner, __, rest = param[8:].partition(")")
        inner = inner.strip()
        # This should be a parameter name that's been specified for the module and must be one that was expanded
        # with alternatives
        # Look up the parameter name in the expanded params
        exp_param = dict(expanded_params).get(inner, None)
        if exp_param is None:
            raise ValueError("parameter '%s' either was not specified for the module or did not have alternative "
                             "values, so we can't take a variable value from the name of its alternative ('altname()')"
                             % inner)
        alt_value, alt_name = exp_param
        # If the alternative was given a name, use it; otherwise use its value
        val = alt_name if alt_name is not None else alt_value
    elif param.startswith("map("):
        rest = param[4:].strip()
        # The first argument should be a value to apply the map to, which may be a variable, or any other value
        to_map_val, rest = _parse_modvar_param(rest, vars, expanded_params, variables_from_inputs)
        # It could end up being a list of values, in which case we apply to map to each
        rest = rest.strip()
        if not rest.startswith(","):
            raise ValueError("map(val, mapping) must take two arguments: the second is the mapping to apply")
        rest = rest[1:].strip()
        # A map is specified as the argument
        # Parse it incrementally
        var_map = {}
        default_mapping = None
        while True:
            rest = rest.strip()
            if rest.startswith(")"):
                # Closing bracket: end of map
                rest = rest[1:]
                break
            # The next bit defines the value we're mapping from
            # Usually it will be a literal (quoted) string, but it doesn't have to be
            # Allow for a special '*' value to denote a default case
            if rest.startswith("*"):
                rest = rest[1:].strip()
                from_val = None
            else:
                from_val, rest = _parse_modvar_param(rest, vars, expanded_params, variables_from_inputs)
                rest = rest.strip()
            # This should be followed by a "->"
            if not rest.startswith("->"):
                raise ValueError("syntax error in map: expected '->', but got '%s'" % rest)
            rest = rest[2:].strip()
            # The next bit is the value we map to
            to_val, rest = _parse_modvar_param(rest, vars, expanded_params, variables_from_inputs)

            if from_val is None:
                # Set what the default mapping is, if the given value doesn't match any of the other mappings
                default_mapping = to_val
            else:
                # The normal case
                # Allow the LHS of the mapping to be a list and match each of its elements
                if type(from_val) is not list:
                    from_val = [from_val]
                for from_val_item in from_val:
                    var_map[from_val_item] = to_val
            rest = rest.strip()
            # Next we just go on to the following mapping, without any separator

        # Now we apply the mapping
        # If the input we're applying to is a list, map each item in the list and return a list
        def _do_map(v):
            if v not in var_map:
                # Don't know what to map this to
                if default_mapping is not None:
                    # Use the specified default
                    return default_mapping
                else:
                    # No default value
                    raise ValueError("mapping got unknown input value '%s' and has no default ('*') mapping" % v)
            else:
                return var_map[v]

        if type(to_map_val) is list:
            val = [_do_map(item) for item in to_map_val]
        else:
            val = _do_map(to_map_val)
    elif param.startswith("join("):
        # Allows list variables to be joined on an arbitrary joiner
        rest = param[5:]
        # The first argument should be a string to be used as the joiner
        joiner, rest = _parse_modvar_param(rest, vars, expanded_params, variables_from_inputs)
        if type(joiner) is list:
            raise ValueError("first argument to join() function should be a string to use as the joiner. Got a list")
        rest = rest.lstrip()
        if not rest.startswith(","):
            raise ValueError("join() expects 2 arguments: a joiner and a list to join")
        rest = rest[1:].lstrip()
        join_list, rest = _parse_modvar_param(rest, vars, expanded_params, variables_from_inputs)
        if not type(join_list) is list:
            raise ValueError("second argument to join() function must be a list. Got: %s" % join_list)
        rest = rest.lstrip()
        if not rest.startswith(")"):
            raise ValueError("expected closing ) after join's args")
        rest = rest[1:]
        # Now perform the actual join
        val = joiner.join(join_list)
    elif param.startswith("len("):
        # Calculate the length of a list
        rest = param[4:]
        # The only argument should be a list
        len_list, rest = _parse_modvar_param(rest, vars, expanded_params, variables_from_inputs)
        if not type(len_list) is list:
            raise ValueError("argument to len() function must be a list. Got: %s" % len_list)
        rest = rest.lstrip()
        if not rest.startswith(")"):
            raise ValueError("expected closing ) after len's arg")
        rest = rest[1:]
        # Just compute the length of the list, which should be a string for future use
        val = "{}".format(len(len_list))
    else:
        match = int_literal_re.search(param)
        if match:
            # Int literals are not actually returned as ints, just as strings
            # However, so we don't require them to be surrounded by quotes, we catch them here, before var processing
            val = param[:match.end()]
            rest = param[match.end():]
        else:
            # Not any of the special values / functions, must be a variable name
            match = var_name_re.search(param)
            if match is None:
                raise ValueError("could not parse variable name at start of '%s'" % param)
            var_name = param[:match.end()]
            rest = param[match.end():]
            # Allow this to be in the form 'input_name.variable_name'
            if "." in var_name:
                input_name, __, var_name = var_name.partition(".")
                if input_name not in variables_from_inputs:
                    raise ValueError("tried to get variable '%s' from input '%s', but could not find that input. "
                                     "Available inputs are: %s" %
                                     (var_name, input_name, ", ".join(variables_from_inputs.keys())))
                elif var_name not in variables_from_inputs[input_name]:
                    raise ValueError("tried to get variable '%s' from input '%s', but the input module doesn't have a "
                                     "variable of that name" %
                                     (var_name, input_name))
                var_val = variables_from_inputs[input_name][var_name]
            else:
                if var_name not in vars:
                    raise ValueError("unknown module variable '%s'" % var_name)
                var_val = vars[var_name]

            # If it's followed by a '[', the var's value should be a list, which we select an item from
            if rest.startswith("["):
                if type(var_val) is not list:
                    raise ValueError("[]-expression can only be applied to list-type modvar expressions")

                rest = rest[1:].lstrip()
                # Parse the next bit, allowing the list item specifier itself to be an expression
                list_item_spec, rest = _parse_modvar_param(rest, vars, expanded_params, variables_from_inputs)
                rest = rest.lstrip()
                # Expect a closing bracket after the specifier
                if not rest.startswith("]"):
                    raise ValueError("expected closing ] after list-item specifier")
                rest = rest[1:]

                if type(list_item_spec) is list:
                    raise ValueError("cannot use a list to select an item from a list")
                # The value should be an int (in string form)
                try:
                    list_item_spec = int(list_item_spec)
                except ValueError:
                    raise ValueError("list-item specifier must be an integer: got '%s'" % list_item_spec)

                val = var_val[list_item_spec]
            else:
                # Use the result of the expression as the value to return
                val = var_val

    return val, rest


def substitute_modvars(options, modvars, expanded_params, variables_from_inputs):
    for key, val in options.items():
        val = substitute_modvars_in_value(key, val, modvars, expanded_params, variables_from_inputs)
        # Make the substitution in the parameters
        options[key] = val


def substitute_modvars_in_value(key, val, modvars, expanded_params, variables_from_inputs, list_action="error"):
    # list_action specifies what happens if we try to substitute a modvar expression that evaluates to a list
    # The default behaviour 'error' simply raises an error
    # Use 'expand' to expand the result into a list, covering all the alternatives
    val_parts = [val]

    # Note that we may have multiple modvar expressions in the same option
    while "$(" in val_parts[-1]:
        before_modvar, __, modvar_onwards = val_parts[-1].partition("$(")

        # Replace the modvar expression by processing it in the standard way
        # This should process everything up to the end of the substitution
        try:
            modvar_result, rest = _parse_modvar_param(
                modvar_onwards, modvars, expanded_params, variables_from_inputs
            )
        except ValueError as e:
            raise PipelineConfigParseError("could not parse module variable expression '%s = %s': %s" % (key, val, e))
        # The next thing should be the closing bracket after the substitution expression
        # i.e. the closer of $(...)
        rest = rest.lstrip()
        if len(rest) == 0:
            raise PipelineConfigParseError("reached end of parameter before finding closing bracket "
                                           "of modvar substitution $(...): {}".format(val))
        elif rest[0] != ")":
            raise PipelineConfigParseError("expected closing bracket after modvar substitution $(...), but "
                                           "got '%s' in parameter: %s" % (rest[0], val))
        # Modvar expressions can evaluate to lists, but we can't use them in substitutions
        if type(modvar_result) is list:
            if list_action == "expand":
                # Expanding now is inefficient
                # Instead, perform all var substs and then expand all the lists
                val_parts.pop()
                val_parts.extend([before_modvar, modvar_result, rest[1:]])
            else:
                raise PipelineConfigParseError("tried to substitute a modvar expression that evaluates to a list of "
                                               "values into a string: %s" % ", ".join(modvar_result))
        else:
            # Include everything that comes after the closing bracket as well
            val_parts[-1] = "%s%s%s" % (before_modvar, modvar_result, rest[1:])

    if list_action == "expand":
        # Expand out all combinations of list values
        def _expand(prts):
            if len(prts) == 0:
                return [""]
            elif type(prts[0]) is list:
                return ["%s%s" % (part0, rec) for part0 in prts[0] for rec in _expand(prts[1:])]
            else:
                return ["%s%s" % (prts[0], rec) for rec in _expand(prts[1:])]
        return _expand(val_parts)
    else:
        return "".join(val_parts)


class ParameterTyingError(Exception):
    pass


def var_substitute(option_val, vars):
    try:
        return option_val % vars
    except KeyError as e:
        raise PipelineConfigParseError("error making substitutions in %s: var %s not specified" % (option_val, e))
    except BaseException as e:
        raise PipelineConfigParseError("error (%s) making substitutions in %s: %s" % (type(e).__name__, option_val, e))


class PipelineConfigParseError(Exception):
    """ General problems interpreting pipeline config """
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        self.explanation = kwargs.pop("explanation", None)
        super(PipelineConfigParseError, self).__init__(*args, **kwargs)


class PipelineStructureError(Exception):
    """ Fundamental structural problems in a pipeline. """
    def __init__(self, *args, **kwargs):
        self.explanation = kwargs.pop("explanation", None)
        super(PipelineStructureError, self).__init__(*args, **kwargs)


class PipelineCheckError(Exception):
    """ Error in the process of explicitly checking a pipeline for problems. """
    def __init__(self, cause, *args, **kwargs):
        self.explanation = kwargs.pop("explanation", None)
        super(PipelineCheckError, self).__init__(*args, **kwargs)
        self.cause = cause


def preprocess_config_file(filename, variant="main", initial_vars={}):
    """
    Workhorse of the initial part of config file reading. Deals with all of our custom stuff for pipeline
    configs, such as preprocessing directives and includes.

    :param filename: file from which to read main config
    :param variant: name of a variant to load. The default (`main`) loads the main variant, which always exists
    :param initial_vars: variable assignments to make available for substitution. This will be added to by any
        `vars` sections that are read.
    :return: tuple: raw config dict; list of variants that could be loaded; final vars dict; list of filenames
        that were read, including included files; dict of docstrings for each config section
    """
    copies = OrderedDict()
    try:
        config_sections, available_variants, vars, all_filenames, section_docstrings, abstract = \
            _preprocess_config_file(filename, variant=variant, copies=copies, initial_vars=initial_vars)
    except IOError as e:
        raise PipelineConfigParseError("could not read config file %s: %s" % (filename, e))
    # If the top-level config file was marked abstract, complain: it shouldn't be run itself
    if abstract:
        raise PipelineConfigParseError("config file %s is abstract: it shouldn't be run itself, but included in "
                                       "another config file" % filename)
    config_sections_dict = OrderedDict(config_sections)

    # Copy config values according to copy directives
    for target_section, source_sections in copies.items():
        # There may be multiple source sections: process in order of directives, so later ones override earlier
        copy_values = {}
        for source_section, exceptions in source_sections:
            if source_section not in config_sections_dict:
                raise PipelineConfigParseError("copy directive in [%s] referred to unknown module '%s'" %
                                               (target_section, source_section))
            source_settings = copy.copy(config_sections_dict[source_section])
            for exception in exceptions:
                if exception not in source_settings:
                    raise PipelineConfigParseError("copy directive exception referred to parameter that wasn't "
                                                   "in the source section: %s" % exception)
                del source_settings[exception]
            # Accumulate values to the copied into target section
            copy_values.update(source_settings)
        # Values set in section itself take precedence over those copied
        copy_values.update(config_sections_dict[target_section])
        # Replace the settings for this module
        config_sections = [(sect, copy_values) if sect == target_section else (sect, settings)
                           for (sect, settings) in config_sections]
        # UPDATE the sections dict so we can subsequently copy from this module
        config_sections_dict = OrderedDict(config_sections)

    if "pipeline" in section_docstrings:
        del section_docstrings["pipeline"]
    if "vars" in section_docstrings:
        del [section_docstrings["vars"]]

    return config_sections, available_variants, vars, all_filenames, section_docstrings


def _preprocess_config_file(filename, variant="main", copies={}, initial_vars={}):
    # Read in the file
    config_lines = []
    available_variants = set([])
    sub_configs = []
    sub_vars = []
    all_filenames = [os.path.abspath(filename)]
    current_section = None
    # Keep the last comments in a buffer so that we can grab those that were just before a section start
    comment_memory = []
    section_docstrings = {}
    # File will be marked abstract if an abstract directive is encountered
    abstract = False

    directive_re = re.compile(r"^%%\s*(?P<dir>\S+)(\s(?P<rest>.*))?$")

    with io.open(filename, "r", encoding="utf-8") as f:
        # ConfigParser can read directly from a file, but we need to pre-process the text
        for line in f:
            line = line.rstrip(u"\n")
            if line.startswith("%%"):
                # Directive: process this now

                dir_match = directive_re.match(line)
                if dir_match is None:
                    raise PipelineConfigParseError("invalid directive line: %s" % line)

                # Don't strip whitespace from the remainder of the line, as it may be needed
                # The first space after the directive is, however, ignored, seeing as it's needed to end the dir
                directive = dir_match.groupdict()["dir"]
                rest = dir_match.groupdict()["rest"] or ""
                directive = directive.lower()

                # Special notation for variants to make config files more concise/readable
                if directive[0] == "(":
                    # Treat (x) as equivalent to variant:x
                    # Transform it to share processing with canonical version below
                    if directive[-1] != ")":
                        raise PipelineConfigParseError("unmatched bracket in bracket notation for variant directive: "
                                                       "'%s' (in line: %s)" % (directive, line))
                    directive = "variant:%s" % directive[1:-1]

                if directive.lower() == "novariant":
                    # Include this line only if loading the main variant
                    if variant == "main":
                        config_lines.append(rest)
                elif directive.lower().startswith("variant:"):
                    variant_conds = directive[8:].strip().split(",")
                    # Line conditional on a specific variant: include only if we're loading that variant
                    if variant in variant_conds:
                        config_lines.append(rest)
                    # Keep a list of all available variants
                    available_variants.update(variant_conds)
                elif directive.lower().startswith("variant"):
                    raise PipelineConfigParseError("variant directive must specify a variant name, as 'variant:<name>'")
                elif directive == "include":
                    # Include another file, given relative to this one
                    relative_filename = rest.strip("\n ")
                    include_filename = os.path.abspath(os.path.join(os.path.dirname(filename), relative_filename))
                    # Run preprocessing over that file too, so we can have embedded includes, etc
                    try:
                        # Ignore abstract flag of included file: it's allowed to be abstract, since it's been included
                        incl_config, incl_variants, incl_vars, incl_filenames, incl_section_docstrings, __ = \
                            _preprocess_config_file(include_filename, variant=variant, copies=copies,
                                                    initial_vars=initial_vars)
                    except IOError as e:
                        raise PipelineConfigParseError("could not find included config file '%s': %s" %
                                                       (relative_filename, e))
                    all_filenames.extend(incl_filenames)
                    # Save this subconfig and incorporate it later
                    # Note what the current section is, so we include it in the right order
                    sub_configs.append((include_filename, incl_config, current_section))
                    # Also save vars section, which may override variables that were defined earlier
                    sub_vars.append(incl_vars)
                    available_variants.update(incl_variants)
                    section_docstrings.update(incl_section_docstrings)
                elif directive == "copy":
                    # Copy config values from another section
                    # For now, just store a list of sections to copy from: we'll do the copying later
                    source_section, __, rest = rest.partition(" ")
                    # The directive might also specify settings that shouldn't be copied
                    exceptions = rest.strip().split()
                    copies.setdefault(current_section, []).append((source_section, exceptions))
                elif directive == "abstract":
                    # Mark this file as being abstract (must be included)
                    abstract = True
                else:
                    raise PipelineConfigParseError("unknown directive '%s' used in config file" % directive)
                comment_memory = []
            else:
                if line.startswith(u"["):
                    # Track what section we're in at any time
                    current_section = line.strip(u"[] \n")
                    # Take the recent comments to be a docstring for the section
                    section_docstrings[current_section] = u"\n".join(comment_memory)
                    comment_memory = []
                elif line.startswith(u"#"):
                    # Don't need to filter out comments, because the config parser handles them, but grab any that
                    # were just before a section to use as a docstring
                    comment_memory.append(line.lstrip(u"#").strip(u" \n"))
                else:
                    # Reset the comment memory for anything other than comments
                    comment_memory = []
                config_lines.append(line)

    # Parse the result as a config file
    config_parser = RawConfigParser()
    try:
        config_parser.read_string(u"\n".join(config_lines), source=filename)
    except configparser.Error as e:
        raise PipelineConfigParseError("could not parse config file %s. %s" % (filename, e))

    # If there's a "vars" section in this config file, remove it now and return it separately
    if config_parser.has_section(u"vars"):
        # Do variable substitution within the vars, using the initial vars and allowing vars to substitute into
        #  subsequent ones
        vars = copy.copy(initial_vars)
        for key, val in config_parser.items(u"vars"):
            key, val = key, var_substitute(val, vars)
            vars[key] = val
    else:
        vars = {}
    # If there were "vars" sections in included configs, allow them to override vars in this one
    for sub_var in sub_vars:
        vars.update(sub_var)

    config_sections = [
        (section, OrderedDict(config_parser.items(section))) for section in config_parser.sections() if section != u"vars"
    ]
    # Add in sections from the included configs
    for subconfig_filename, subconfig, include_after in sub_configs:
        # Check there's no overlap between the sections defined in the subconfig and those we already have
        overlap_sections = set(map(itemgetter(0), config_sections)) & set(map(itemgetter(0), subconfig))
        if overlap_sections:
            raise PipelineStructureError("section '%s' defined in %s has already be defined in an including "
                                         "config file" % (" + ".join(overlap_sections), subconfig_filename))
        # Find the index where we'll include this
        after_index = next((i for (i, (sec, conf)) in enumerate(config_sections) if sec == include_after))
        config_sections = config_sections[:after_index+1] + subconfig + config_sections[after_index+1:]

    # Config parser permits values that span multiple lines and removes indent of subsequent lines
    # This is good, but we don't want the newlines to be included in the values
    config_sections = [
        (section, OrderedDict(
            (key, val.replace(u"\n", u"")) for (key, val) in section_config.items()
        )) for (section, section_config) in config_sections
    ]

    # Don't include "main" variant in available variants
    available_variants.discard("main")
    return config_sections, available_variants, vars, all_filenames, section_docstrings, abstract


def _check_valid_alt_name(name):
    """ Check that the given string doesn't contain substrings disallowed in names of module alternatives """
    for disallowed in ["[", "]", ",", "|", "\n"]:
        if disallowed in name:
            if disallowed == "\n":
                disallowed = "newline"
            raise ValueError("module alternative name '{}' is invalid: alt names may not "
                             "include '{}'".format(name, disallowed))


_non_mod_name_char = re.compile(r"[\],*|]")


def _expand_alt_names_list(val):
    """
    Checks through a string for a list of alt names within []s after a module name.
    These get expanded into a list of repeats of the module name, covering each of
    the alt names in a list.

    E.g. "mymod[alt1,alt2,alt3],mymod2" -> "mymod[alt1],mymod[alt2],mymod[alt3],mymod2"

    """
    index = 0
    while "[" in val[index:]:
        open_bracket = val.index("[", index)
        close_bracket = val.find("]", open_bracket)
        if close_bracket == -1:
            # No matching closing bracket
            # Don't complain here: an error will arise somewhere else
            return val
        if "," in val[open_bracket+1:close_bracket]:
            # Get the main module name by seaching backwards from the [ for non-module name strings
            non_mod_chars = _non_mod_name_char.findall(val[:open_bracket])
            if len(non_mod_chars) == 0:
                mod_start = 0
            else:
                mod_start = non_mod_chars[-1].end() + 1
            mod_name = val[mod_start:open_bracket]
            # Get the list of alt names
            alt_names = val[open_bracket+1:close_bracket].split(",")
            # Expand the list and reconstruct the string around it
            val = val[:mod_start] + \
                  ",".join("{}[{}]".format(mod_name, alt_name) for alt_name in alt_names) + \
                  val[close_bracket+1:]
        index = close_bracket+1
    return val


def check_for_cycles(pipeline):
    """ Basic cyclical dependency check, always run on pipeline before use. """
    # Build a mapping representing module dependencies
    dep_map = dict(
        (module_name, pipeline[module_name].dependencies) for module_name in pipeline.modules
    )

    def _search(node, check_for):
        if node not in dep_map:
            # Error in the config, but this should be picked up by other checks, not here
            return False
        elif len(dep_map[node]) == 0:
            # No dependencies: no cycle found
            return False
        elif check_for in dep_map[node]:
            # Found: this is a cycle
            return True
        else:
            # No cycle here: continue recursively to search for the node
            return any(_search(dep, check_for) for dep in dep_map[node])

    for module in pipeline.modules:
        # Search recursively through this module's dependencies for itself
        if _search(module, module):
            # Found a cycle
            raise PipelineStructureError("the pipeline turned into a loop! Module %s was found among its own "
                                         "transitive dependencies" % module)


def check_release(release_str):
    """ Check a release name against the current version of Pimlico to determine whether we meet the requirement. """
    from pimlico import __version__
    current_major_release, __, current_minor_release = __version__.partition(".")
    required_major_release, __, required_minor_release = release_str.partition(".")
    current_major_release, required_major_release = int(current_major_release), int(required_major_release)

    current_rc = current_minor_release.endswith("rc")
    if current_rc:
        # This is a release candidate
        # Acceptable for minor versions below this or an identical RC, but not the (non-RC) same version
        current_minor_release = current_minor_release[:-2]
    given_rc = required_minor_release.endswith("rc")
    if given_rc:
        # RC required
        # Allow minor versions above it, or an identical RC
        required_minor_release = required_minor_release[:-2]

    if current_major_release < required_major_release:
        raise PipelineStructureError("config file was written for a later version of Pimlico than the one you're "
                                     "running. You need to update Pimlico (or check out a later release), as there "
                                     "could be backwards-incompatible changes between major versions. Running version "
                                     "%s, required version %s" % (__version__, release_str))
    elif current_major_release > required_major_release:
        raise PipelineStructureError("config file was written for an earlier version of Pimlico than the one you're "
                                     "running. You need to check out an earlier release, as the behaviour of Pimlico "
                                     "could be very different to when the config file was written. Running version "
                                     "%s, required version %s" % (__version__, release_str))

    # Right major version
    # Check we're not running an earlier minor version
    remaining_current = current_minor_release
    remaining_given = required_minor_release

    higher_than_required = False
    while len(remaining_given):
        if len(remaining_current) == 0:
            # Given version has the same prefix, but specifies more subversions, so is a later release
            raise PipelineStructureError("config file was written for a later (minor) version of Pimlico than the "
                                         "one you're running. You need to use >= v%s to run this config "
                                         "file (and not > %s). Currently using %s" %
                                         (release_str, required_major_release, __version__))

        current_part, __, remaining_current = remaining_current.partition(".")
        given_part, __, remaining_given = remaining_given.partition(".")

        if int(current_part) > int(given_part):
            # Using a higher minor version than required: stop checking
            higher_than_required = True
            break
        elif int(current_part) < int(given_part):
            raise PipelineStructureError("config file was written for a later (minor) version of Pimlico than the "
                                         "one you're running. You need to use >= v%s to run this config "
                                         "file (and not > %s). Currently using %s" %
                                         (release_str, required_major_release, __version__))
        # Otherwise using same version at this level: go down to next level and check

    if len(remaining_current) > 0:
        # Given version has the same prefix, but current version has more subversions, so is a later release
        higher_than_required = True

    if not higher_than_required:
        # Allow equal minor versions, except in the case where the supplied version is only a RC
        if current_rc and not given_rc:
            raise PipelineStructureError("config file was written for the version of Pimlico you're running, but "
                                         "not a release candidate. Require %s. "
                                         "Currently only using a release candidate, %s" %
                                         (release_str, __version__))


def check_pipeline(pipeline):
    """
    Checks a pipeline over for metadata errors, cycles, module typing errors and other problems.
    Called every time a pipeline is loaded, to check the whole pipeline's metadata is in order.

    Raises a :class:`PipelineCheckError` if anything's wrong.

    """
    # Basic metadata has already been loaded if we've got this far
    # Check the pipeline for cycles: this will raise an exception if a cycle is found
    try:
        check_for_cycles(pipeline)
    except PipelineStructureError as e:
        raise PipelineCheckError(e, "cycle check failed")

    # Check the types of all the output->input connections
    for module in pipeline.modules:
        mod = pipeline[module]
        try:
            mod.typecheck_inputs()
        except PipelineStructureError as e:
            raise PipelineCheckError(e, "Input typechecking for module '%s' failed: %s" % (module, e),
                                     explanation=e.explanation)


def get_dependencies(pipeline, modules, recursive=False, sources=False):
    """
    Get a list of software dependencies required by the subset of modules given.

    If recursive=True, dependencies' dependencies are added to the list too.

    :param pipeline:
    :param modules: list of modules to check. If None, checks all modules
    """
    if modules is None:
        modules = pipeline.modules

    # Add to the list of modules any that will be executed along with the specified ones
    modules = remove_duplicates(
        [mod.module_name for module_name in modules for mod in pipeline[module_name].get_all_executed_modules()]
    )

    dependencies = []
    # Keep track of where the dependencies came from
    dependency_module_sources = {}

    for module_name in modules:
        module = pipeline[module_name]
        module_dependencies = []
        # Get any software dependencies for this module
        module_dependencies.extend(module.get_software_dependencies())
        # Also get dependencies of the input datatypes
        module_dependencies.extend(module.get_input_software_dependencies())
        # And dependencies of the output datatypes, since we assume they are needed to write the output
        module_dependencies.extend(module.get_output_software_dependencies())

        if recursive:
            # Also check whether the deps we've just added have their own dependencies
            for dep in list(module_dependencies):
                # These need to be installed before the above
                module_dependencies = dep.all_dependencies() + module_dependencies

        dependencies.extend(module_dependencies)
        for dep in module_dependencies:
            dependency_module_sources.setdefault(dep, []).append(module_name)

    # We may want to do something cleverer to remove duplicate dependencies, but at least remove any duplicates
    #  of exactly the same object and any that provide a comparison operator that says they're equal
    dependencies = remove_duplicates(dependencies)

    if sources:
        return dependencies, dependency_module_sources
    else:
        return dependencies


def print_missing_dependencies(pipeline, modules):
    """
    Check runtime dependencies for a subset of modules and output a table of missing dependencies.

    :param pipeline:
    :param modules: list of modules to check. If None, checks all modules
    :return: True if no missing dependencies, False otherwise
    """
    deps, dep_sources = get_dependencies(pipeline, modules, sources=True)
    missing_dependencies = [dep for dep in deps if not dep.available(pipeline.local_config)]

    if len(missing_dependencies):
        print("Some library dependencies were not satisfied\n")
        auto_installable_modules = []
        auto_installable_deps = []
        for dep in missing_dependencies:
            print(title_box(dep.name.capitalize()))
            # Print the list of problems and check at the same time whether it's auto-installable
            mod_auto_installable = print_dependency_leaf_problems(dep, pipeline.local_config)
            # Output any installation notes provided by the dependency
            notes = dep.installation_notes().strip()
            if len(notes):
                print(textwrap.fill(notes, 80))

            if mod_auto_installable:
                auto_installable_modules.extend(dep_sources[dep])
                auto_installable_deps.append(dep)
            print()

        auto_installable_deps = remove_duplicates(auto_installable_deps)

        if len(auto_installable_deps):
            print("%s missing dependencies are automatically installable: %s" % (
                "All" if len(missing_dependencies) == len(auto_installable_deps) else "Some",
                ", ".join(dep.name for dep in auto_installable_deps)
            ))
            try:
                install_now = input("Do you want to install these now? [y/N] ").lower().strip() == "y"
            except EOFError:
                # We get an EOF if the user enters it, or if we're not running in interactive mode
                install_now = False

            if install_now:
                uninstalled = check_and_install(auto_installable_deps, pipeline.local_config)
                if len(uninstalled):
                    print("Installation failed")
                    return False
                else:
                    # If we were only able to install some, return False so we know some are still unsatisfied
                    return len(missing_dependencies) == len(auto_installable_deps)
            else:
                print("Modules with automatically installable dependencies: %s" % ", ".join(auto_installable_modules))
                print("Use 'install' command to install all automatically installable dependencies")
        return False
    else:
        return True


def print_dependency_leaf_problems(dep, local_config):
    auto_installable = False
    sub_deps = dep.dependencies()
    if len(sub_deps) and not all(sub_dep.available(local_config) for sub_dep in sub_deps):
        print("Dependency '%s' not satisfied because of problems with its own dependencies" % dep.name)
        # If this dependency has its own dependencies and they're not available, print their problems
        for sub_dep in dep.dependencies():
            if not sub_dep.available(local_config):
                print("'%s' depends on '%s', which is not available" % (dep.name, sub_dep.name))
                auto_installable = print_dependency_leaf_problems(sub_dep, local_config) or auto_installable
    else:
        # The problems are generated by this dependency, not its own dependencies
        print("Dependency '%s' not satisfied because of the following problems:" % dep.name)
        for problem in dep.problems(local_config):
            print(" - %s" % problem)

        instructions = dep.installation_instructions()
        if dep.installable():
            print("Can be automatically installed using install command")
            auto_installable = True
        else:
            print("Cannot be installed automatically")
        # If instructions are available, print them, even if the dependency is automatically installable
        if instructions:
            instructions = instructions.strip(" \n")
            print("\nInstallation instructions:\n{}\n".format(
                "\n".join("  {}".format(line) for line in instructions.splitlines())
            ))
    return auto_installable
