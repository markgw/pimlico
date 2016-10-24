# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Reading of pipeline config from a file into the data structure used to run and manipulate the pipeline's data.
"""
import ConfigParser
import copy
import os
import sys
from ConfigParser import SafeConfigParser, RawConfigParser
from cStringIO import StringIO
from operator import itemgetter

from pimlico import PIMLICO_ROOT, PROJECT_ROOT, OUTPUT_DIR
from pimlico.datatypes.base import load_datatype, DatatypeLoadError
from pimlico.utils.core import remove_duplicates
from pimlico.utils.format import title_box
from pimlico.utils.logging import get_console_logger

__all__ = [
    "PipelineConfig", "PipelineConfigParseError", "PipelineStructureError", "preprocess_config_file",
    "check_for_cycles", "check_release", "check_pipeline", "get_dependencies", "print_missing_dependencies",
    "print_dependency_leaf_problems", "PipelineCheckError",
]

REQUIRED_LOCAL_CONFIG = ["short_term_store", "long_term_store"]


class PipelineConfig(object):
    """
    Main configuration for a pipeline, read in from a config file.

    For details on how to write config files that get read by this class, see :doc:`/core/config`.

    """
    def __init__(self, name, pipeline_config, local_config,
                 filename=None, variant="main", available_variants=[], log=None, all_filenames=None,
                 module_aliases={}):
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

        # Pipeline is empty to start with
        self.module_infos = {}
        self.module_order = []

        # Certain standard system-wide settings, loaded from the local config
        self.long_term_store = os.path.join(self.local_config["long_term_store"], self.name, self.variant)
        self.short_term_store = os.path.join(self.local_config["short_term_store"], self.name, self.variant)
        # Number of processes to use for anything that supports multiprocessing
        self.processes = int(self.local_config.get("processes", 1))

        # Get paths to add to the python path for the pipeline
        # Used so that a project can specify custom module types and other python code outside the pimlico source tree
        if "python_path" in self.pipeline_config:
            # Paths should all be specified relative to the config file's directory
            additional_paths = [self.path_relative_to_config(path) for path in
                                self.pipeline_config["python_path"].split(":") if path]
            # Add these paths for the python path, so later code will be able to import things from them
            sys.path.extend(additional_paths)

        self._module_schedule = None

        self._dependency_cache = None

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

    def get_dependent_modules(self, module_name, recurse=False):
        """
        Return a list of the names of modules that depend on the named module for their inputs.

        :param recurse: include all transitive dependents, not just those that immediately depend on the module.
        """
        dependents = [mod for (mod, dependencies) in self.module_dependencies.items() if module_name in dependencies]
        if recurse:
            # Fetch the dependents of each of the dependents of this module
            # This should never result in an infinite loop, since we check for cycles in the graph
            # If the check hasn't been run, things might go bad!
            for dep_mod in dependents:
                dependents.extend(self.get_dependent_modules(dep_mod, recurse=True))
        return remove_duplicates(dependents)

    def append_module(self, module_info):
        """
        Add a moduleinfo to the end of the pipeline. This is mainly for use while loaded a pipeline from a
        config file.

        """
        self.module_infos[module_info.module_name] = module_info
        self.module_order.append(module_info.module_name)
        # Check that the moduleinfo knows what pipeline it's in (it's usually already set by this point)
        module_info.pipeline = self

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

    @staticmethod
    def load(filename, local_config=None, variant="main", override_local_config={}):
        """
        Main function that loads a pipeline from a config file.

        :param filename: file to read config from
        :param local_config: location of local config file, where we'll read system-wide config
        :param variant: pipeline variant to load
        :param override_local_config: extra configuration values to override the system-wide config
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

        local_config_data = PipelineConfig.load_local_config(filename=local_config, override=override_local_config)

        # Special vars are available for substitution in all options, including other vars
        special_vars = {
            "project_root": PROJECT_ROOT,
            "pimlico_root": PIMLICO_ROOT,
            "output_dir": OUTPUT_DIR,
            "long_term_store": local_config_data["long_term_store"],
            "short_term_store": local_config_data["short_term_store"],
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
        raw_module_options = dict(
            (
                section,
                # Perform our own version of interpolation here, substituting values from the vars section into others
                dict((key, var_substitute(val, vars)) for (key, val) in config_section_dict[section].items())
            ) for section in module_order
        )

        # Check that we have a module for every alias
        for alias, alias_target in aliases.iteritems():
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
            all_filenames=all_filenames, module_aliases=aliases
        )

        # Now we're ready to try loading each of the module infos in turn
        module_infos = {}
        loaded_modules = []
        # Construct a mapping from the section names as written to expanded sections and the other way
        original_to_expanded_sections = {}
        expanded_to_original_sections = {}

        for module_name in module_order:
            try:
                module_config = raw_module_options[module_name]

                # Work out what the previous module was, so that we can use it as a default connection
                previous_module_name = loaded_modules[-1] if len(loaded_modules) else None

                # Load the module info class for the declared type of the module in the config
                if "type" not in module_config:
                    raise PipelineConfigParseError("module %s does not specify a type" % module_name)
                try:
                    # First see if this is a datatype
                    datatype_class = load_datatype(module_config["type"])
                except DatatypeLoadError:
                    # Not a datatype
                    module_info_class = load_module_info(module_config["type"])
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
                                       for input_name in dict(module_info_class.module_inputs).keys()]
                    missing_inputs = [name for name in required_inputs if name not in module_config]

                for input_key in missing_inputs:
                    # Supply the previous module in the config file as default for missing inputs
                    if previous_module_name is None:
                        raise PipelineStructureError("module '%s' has no input specified, but there's no previous "
                                                     "module to use as default" % module_name)
                    else:
                        # By default, connect to the default output from the previous module
                        module_config[input_key] = previous_module_name

                # Allow document map types to be used as filters simply by specifying filter=T
                filter_type = str_to_bool(module_config.pop("filter", ""))
                # Check for the tie_alts option, which causes us to tie together lists of alternatives instead
                # of taking their product
                tie_alts = str_to_bool(module_config.pop("tie_alts", ""))

                # Parameters and inputs can be given multiple values, separated by |s
                # In this case, we need to multiply out all the alternatives, to make multiple modules
                # Check whether any of the inputs to this module come from a previous module that's been expanded into
                # multiple. If so, give this model alternative inputs to cover them all
                for input_opt in [key for key in module_config.keys() if key == "input" or key.startswith("input_")]:
                    new_alternatives = []
                    # It's possible for the value to already have alternatives, in which case we include them all
                    for original_val in module_config[input_opt].split("|"):
                        # If the input connection has more than just a module name, we only modify the module name
                        val_module_name, __, rest_of_val = original_val.partition(".")
                        # If the module name is unknown, this will be a problem, but leave the error handling till later
                        if len(original_to_expanded_sections.get(val_module_name, [])) > 1:
                            # The previous module has been expanded: add all of the resulting modules as alternatives
                            previous_modules = original_to_expanded_sections[val_module_name]
                            # If the previous module names are already in the form module{alt_name}, take the alt_name
                            # from there
                            previous_module_alt_names = [
                                mod[mod.index("[")+1:-1] if "[" in mod else None for mod in previous_modules
                            ]
                            new_alternatives.extend([
                                "{%s}%s" % (alt_name, mod) if alt_name is not None else mod
                                for (mod, alt_name) in zip(previous_modules, previous_module_alt_names)
                            ])
                        else:
                            # Previous module this one takes input from has not been expanded: leave unchanged
                            new_alternatives.append(original_val)
                    module_config[input_opt] = "|".join(new_alternatives)

                # Now look for any options with alternative values and expand them out into multiple module configs
                expanded_module_configs = []
                if any("|" in val for val in module_config.values()):
                    # There are alternatives in this module: expand into multiple modules
                    params_with_alternatives = {}
                    alternative_names = {}
                    fixed_params = {}
                    for key, val in module_config.items():
                        if "|" in val:
                            # Split up the alternatives and allow space around the |s
                            alts = [alt.strip() for alt in val.split("|")]
                            # The alternatives may provide names to identify them by, rather than the param val itself
                            # Get rid of these from the param vals
                            param_vals = [
                                (alt.partition("}")[2], alt[1:alt.index("}")]) if alt.startswith("{")  # Use given name
                                else (alt, alt)  # Use param itself as name
                                for alt in alts
                                ]
                            params_with_alternatives[key] = param_vals
                            # Also pull out the names so we can use them
                            alternative_names[key] = [alt[1:alt.index("}")] if alt.startswith("{") else alt for alt in alts]
                        else:
                            fixed_params[key] = val

                    if len(params_with_alternatives) > 0:
                        if tie_alts:
                            # Don't produce all combinations of alternative values
                            # Instead iterate over each set of alternatives in parallel
                            # For this, each must have the same number of alts
                            alt_nums = [len(alts) for alts in params_with_alternatives.values()]
                            if len(params_with_alternatives) > 1:
                                if not all(num == alt_nums[0] for num in alt_nums):
                                    raise PipelineStructureError("module '%s' has alternative values for multiple "
                                                                 "parameters, but doesn't have the same number of "
                                                                 "alternatives for each (%s): cannot use 'tie_alts' "
                                                                 "behaviour" % ", ".join(str(n) for n in alt_nums))
                            ordered_keys = params_with_alternatives.keys()
                            # Step through the alternative values, picking the same one from each of the parameters
                            alternative_configs = [
                                [(key, params_with_alternatives[key][alt_num]) for key in ordered_keys]
                                for alt_num in range(alt_nums[0])
                            ]
                        else:
                            # Generate all combinations of params that have alternatives
                            alternative_configs = multiply_alternatives(params_with_alternatives.items())
                    else:
                        alternative_configs = [[]]

                    # Generate a name for each
                    alternative_config_names = [
                        "%s[%s]" % (
                            module_name,
                            # If there's only 1 parameter that's varied, don't include the key in the name
                            # If a special name was given, use it; otherwise, this is just the param value
                            params_set[0][1][1] if len(params_set) == 1
                            # If all the params' values happen to have the same name, just use that
                            # (This is common, if they've come from the same alternatives earlier in the pipeline
                                or all(name == params_set[0][1][1] for (key, (val, name)) in params_set)
                            else "~".join("%s=%s" % (key, name) for (key, (val, name)) in params_set)
                        ) for params_set in alternative_configs
                    ]
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
                else:
                    # No alternatives
                    expanded_module_configs.append((module_name, module_config))
                    original_to_expanded_sections[module_name] = [module_name]
                    expanded_to_original_sections[module_name] = module_name

                # Now we create a module info for every expanded module config
                # Often this will just be one, but it could be many, if there are several options with alternatives
                for expanded_module_name, expanded_module_config in expanded_module_configs:
                    # Pass in all other options to the info constructor
                    options_dict = dict(expanded_module_config)
                    try:
                        inputs, optional_outputs, options = module_info_class.process_config(
                            options_dict, module_name=module_name, previous_module_name=previous_module_name)
                    except ModuleOptionParseError, e:
                        raise PipelineConfigParseError("error in '%s' options: %s" % (module_name, e))

                    # Instantiate the module info
                    module_info = module_info_class(
                        expanded_module_name, pipeline, inputs=inputs, options=options,
                        optional_outputs=optional_outputs, docstring=section_docstrings.get(module_name, ""),
                        # Make sure that the module info includes any optional outputs that are used by other modules
                        include_outputs=used_outputs.get(module_name, []),
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
            except ModuleInfoLoadError, e:
                raise PipelineConfigParseError("error loading module metadata for module '%s': %s" % (module_name, e))

        try:
            # Run all type-checking straight away so we know this is a valid pipeline
            check_pipeline(pipeline)
        except PipelineCheckError, e:
            raise PipelineConfigParseError("pipeline loaded, but failed checks: %s" % e, cause=e)

        return pipeline

    @staticmethod
    def load_local_config(filename=None, override={}):
        """
        Load local config parameters. These are usually specified in a `.pimlico` file, but may be overridden
        on the command line, or elsewhere programmatically.

        """
        if filename is None:
            # Use the default locations for local config file
            # May want to add other locations here...
            local_config = [os.path.join(os.path.expanduser("~"), ".pimlico")]
        else:
            local_config = [filename]

        # Load local config file(s)
        for local_filename in local_config:
            if os.path.exists(local_filename):
                local_config_filename = local_filename
                break
        else:
            raise PipelineConfigParseError("could not load a Pimlico configuration file to read local setup from. "
                                           "Tried: %s" % ", ".join(local_config))
        # Read in the local config and supply a section heading to satisfy config parser
        with open(local_config_filename, "r") as f:
            local_text_buffer = StringIO("[main]\n%s" % f.read())

        local_config_parser = SafeConfigParser()
        local_config_parser.readfp(local_text_buffer)
        local_config_data = dict(local_config_parser.items("main"))
        # Allow parameters to be overridden on the command line
        local_config_data.update(override)

        for attr in REQUIRED_LOCAL_CONFIG:
            if attr not in local_config_data:
                raise PipelineConfigParseError("required attribute '%s' is not specified in local config" % attr)
        return local_config_data

    @staticmethod
    def empty(local_config=None, override_local_config={}, override_pipeline_config={}):
        """
        Used to programmatically create an empty pipeline. It will contain no modules, but provides a gateway to
        system info, etc and can be used in place of a real Pimlico pipeline.

        :param local_config: filename to load local config from. If not given, the default locations are searched
        :param override_local_config: manually override certain local config parameters. Dict of parameter values
        :return: the :class:`PipelineConfig` instance
        """
        from pimlico import __version__ as current_pimlico_version

        local_config_data = PipelineConfig.load_local_config(filename=local_config, override=override_local_config)
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
        except PipelineCheckError, e:
            raise PipelineConfigParseError("empty pipeline created, but failed checks: %s" % e, cause=e)

        return pipeline

    def find_data_path(self, path, default=None):
        """
        Given a path to a data dir/file relative to a data store, tries taking it relative to various store base
        dirs. If it exists in a store, that absolute path is returned. If it exists in no store, return None.
        If the path is already an absolute path, nothing is done to it.

        The stores searched are the long-term store and the short-term store, though in the future more valid data
        storage locations may be added.

        :param path: path to data, relative to store base
        :param default: usually, return None if no data is found. If default="short", return path relative to
         short-term store in this case. If default="long", long-term store.
        :return: absolute path to data, or None if not found in any store
        """
        if os.path.isabs(path):
            return path
        try:
            return self.find_all_data_paths(path).next()
        except StopIteration:
            if default == "short":
                return os.path.join(self.short_term_store, path)
            elif default == "long":
                return os.path.join(self.long_term_store, path)
            else:
                return None

    def find_all_data_paths(self, path):
        # If the path is already an absolute path, don't search for the data
        # Just return it if it exists
        if os.path.isabs(path):
            if os.path.exists(path):
                yield path
            return

        for store_base in [self.short_term_store, self.long_term_store]:
            if os.path.exists(os.path.join(store_base, path)):
                yield os.path.join(store_base, path)


def multiply_alternatives(alternative_params):
    if len(alternative_params):
        # Pick a key
        key, vals = alternative_params.pop()
        # Recursively generate all alternatives by other keys
        alternatives = multiply_alternatives(alternative_params)
        # Make a copy of each alternative combined with each val for this key
        return [alt_params + [(key, val)] for val in vals for alt_params in alternatives]
    else:
        # No alternatives left, base case: return an empty list
        return [[]]


def var_substitute(option_val, vars):
    try:
        return option_val % vars
    except KeyError, e:
        raise PipelineConfigParseError("error making substitutions in %s: var %s not specified" % (option_val, e))
    except BaseException, e:
        raise PipelineConfigParseError("error (%s) making substitutions in %s: %s" % (type(e).__name__, option_val, e))


class PipelineConfigParseError(Exception):
    """ General problems interpreting pipeline config """
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        super(PipelineConfigParseError, self).__init__(*args, **kwargs)


class PipelineStructureError(Exception):
    """ Fundamental structural problems in a pipeline. """
    pass


class PipelineCheckError(Exception):
    """ Error in the process of explicitly checking a pipeline for problems. """
    def __init__(self, cause, *args, **kwargs):
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
    copies = {}
    try:
        config_sections, available_variants, vars, all_filenames, section_docstrings, abstract = \
            _preprocess_config_file(filename, variant=variant, copies=copies, initial_vars=initial_vars)
    except IOError, e:
        raise PipelineConfigParseError("could not read config file %s: %s" % (filename, e))
    # If the top-level config file was marked abstract, complain: it shouldn't be run itself
    if abstract:
        raise PipelineConfigParseError("config file %s is abstract: it shouldn't be run itself, but included in "
                                       "another config file" % filename)
    config_sections_dict = dict(config_sections)

    # Copy config values according to copy directives
    for target_section, source_sections in copies.iteritems():
        # There may be multiple source sections: process in order of directives, so later ones override earlier
        copy_values = {}
        for source_section in source_sections:
            if source_section not in config_sections_dict:
                raise PipelineConfigParseError("copy directive in [%s] referred to unknown module '%s'" %
                                               (target_section, source_section))
            # Accumulate values to the copied into target section
            copy_values.update(config_sections_dict[source_section])
        # Remove certain keys that shouldn't be copied
        copy_values = dict((key, val) for (key, val) in copy_values.iteritems()
                           if key not in ["filter", "outputs", "type"] and not key.startswith("input"))
        # Values set in section itself take precedence over those copied
        copy_values.update(config_sections_dict[target_section])
        # Replace the settings for this module
        config_sections = [(sect, copy_values) if sect == target_section else (sect, settings)
                           for (sect, settings) in config_sections]

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

    with open(filename, "r") as f:
        # ConfigParser can read directly from a file, but we need to pre-process the text
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("%% "):
                # Directive: process this now
                directive, __, rest = line[3:].partition(" ")
                if directive.lower() == "novariant":
                    # Include this line only if loading the main variant
                    if variant == "main":
                        config_lines.append(rest.lstrip())
                elif directive.lower().startswith("variant:"):
                    variant_conds = directive[8:].strip().split(",")
                    # Line conditional on a specific variant: include only if we're loading that variant
                    if variant in variant_conds:
                        config_lines.append(rest.lstrip())
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
                    except IOError, e:
                        raise PipelineConfigParseError("could not find included config file '%s': %s" %
                                                       (relative_filename, e))
                    all_filenames.extend(incl_filenames)
                    # Save this subconfig and incorporate it later
                    sub_configs.append((include_filename, incl_config))
                    # Also save vars section, which may override variables that were defined earlier
                    sub_vars.append(incl_vars)
                    available_variants.update(incl_variants)
                    section_docstrings.update(incl_section_docstrings)
                elif directive == "copy":
                    # Copy config values from another section
                    # For now, just store a list of sections to copy from: we'll do the copying later
                    source_section = rest.strip()
                    copies.setdefault(current_section, []).append(source_section)
                elif directive == "abstract":
                    # Mark this file as being abstract (must be included)
                    abstract = True
                else:
                    raise PipelineConfigParseError("unknown directive '%s' used in config file" % directive)
                comment_memory = []
            else:
                if line.startswith("["):
                    # Track what section we're in at any time
                    current_section = line.strip("[] \n")
                    # Take the recent comments to be a docstring for the section
                    section_docstrings[current_section] = "\n".join(comment_memory)
                    comment_memory = []
                elif line.startswith("#"):
                    # Don't need to filter out comments, because the config parser handles them, but grab any that
                    # were just before a section to use as a docstring
                    comment_memory.append(line.lstrip("#").strip(" \n"))
                else:
                    # Reset the comment memory for anything other than comments
                    comment_memory = []
                config_lines.append(line)

    # Parse the result as a config file
    config_parser = RawConfigParser()
    try:
        config_parser.readfp(StringIO("\n".join(config_lines)))
    except ConfigParser.Error, e:
        raise PipelineConfigParseError("could not parse config file %s. %s" % (filename, e))

    # If there's a "vars" section in this config file, remove it now and return it separately
    if config_parser.has_section("vars"):
        # Do variable substitution within the vars, using the initial vars and allowing vars to substitute into
        #  subsequent ones
        vars = copy.copy(initial_vars)
        for key, val in config_parser.items("vars"):
            key, val = key, var_substitute(val, vars)
            vars[key] = val
    else:
        vars = {}
    # If there were "vars" sections in included configs, allow them to override vars in this one
    for sub_var in sub_vars:
        vars.update(sub_var)

    config_sections = [
        (section, dict(config_parser.items(section))) for section in config_parser.sections() if section != "vars"
    ]
    # Add in sections from the included configs
    for subconfig_filename, subconfig in sub_configs:
        # Check there's no overlap between the sections defined in the subconfig and those we already have
        overlap_sections = set(map(itemgetter(0), config_sections)) & set(map(itemgetter(0), subconfig))
        if overlap_sections:
            raise PipelineStructureError("section '%s' defined in %s has already be defined in an including "
                                         "config file" % (" + ".join(overlap_sections), subconfig_filename))
        config_sections.extend(subconfig)

    # Config parser permits values that span multiple lines and removes indent of subsequent lines
    # This is good, but we don't want the newlines to be included in the values
    config_sections = [
        (section, dict(
            (key, val.replace(u"\n", u"")) for (key, val) in section_config.items()
        )) for (section, section_config) in config_sections
    ]

    # Don't include "main" variant in available variants
    available_variants.discard("main")
    return config_sections, available_variants, vars, all_filenames, section_docstrings, abstract


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

    if not higher_than_required:
        # Allow equal minor versions, except in the case where the supplied version is only a RC
        if current_rc and not given_rc:
            raise PipelineStructureError("config file was written for a later (minor) version of Pimlico than the "
                                         "one you're running. You need to use >= v%s to run this config "
                                         "file (and not > %s). Currently only using a release candidate, %s" %
                                         (release_str, required_major_release, __version__))


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
    except PipelineStructureError, e:
        raise PipelineCheckError(e, "cycle check failed")

    # Check the types of all the output->input connections
    try:
        for module in pipeline.modules:
            mod = pipeline[module]
            mod.typecheck_inputs()
    except PipelineStructureError, e:
        raise PipelineCheckError(e, "Input typechecking failed: %s" % e)


def get_dependencies(pipeline, modules, recursive=False):
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
    for module_name in modules:
        module = pipeline[module_name]
        module_dependencies = []
        # Get any software dependencies for this module
        module_dependencies.extend(module.get_software_dependencies())
        # Also get dependencies of the input datatypes
        module_dependencies.extend(module.get_input_software_dependencies())
        dependencies.extend(module_dependencies)
        if recursive:
            # Also check whether the deps we've just added have their own dependencies
            for dep in module_dependencies:
                dependencies.extend(dep.all_dependencies())

    # We may want to do something cleverer to remove duplicate dependencies, but at lest remove any duplicates
    #  of exactly the same object and any that provide a comparison operator that says they're equal
    dependencies = remove_duplicates(dependencies)
    return dependencies


def print_missing_dependencies(pipeline, modules):
    """
    Check runtime dependencies for a subset of modules and output a table of missing dependencies.

    :param pipeline:
    :param modules: list of modules to check. If None, checks all modules
    :return: True if no missing dependencies, False otherwise
    """
    deps = get_dependencies(pipeline, modules)
    missing_dependencies = [dep for dep in deps if not dep.available()]

    if len(missing_dependencies):
        print "Some library dependencies were not satisfied\n"
        auto_installable = False
        for dep in missing_dependencies:
            print title_box(dep.name.capitalize())
            auto_installable = auto_installable or print_dependency_leaf_problems(dep)
            print
        if auto_installable:
            print "Use 'install' command to install all automatically installable dependencies"
        return False
    else:
        return True


def print_dependency_leaf_problems(dep):
    auto_installable = False
    if not all(sub_dep.available() for sub_dep in dep.dependencies()):
        # If this dependency has its own dependencies and they're not available, print their problems
        for sub_dep in dep.dependencies():
            if not sub_dep.available():
                print "'%s' depends on '%s', which is not available" % (dep.name, sub_dep.name)
                auto_installable = auto_installable or print_dependency_leaf_problems(sub_dep)
    else:
        # The problems are generated by this dependency, not its own dependencies
        print "Dependency '%s' not satisfied because of the following problems:" % dep.name
        for problem in dep.problems():
            print " - %s" % problem
        if dep.installable():
            print "Can be automatically installed using install command"
            auto_installable = True
        else:
            print "Cannot be installed automatically"
            instructions = dep.installation_instructions()
            if instructions:
                print instructions
    print
    return auto_installable
