# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Reading of various types of config files, in particular a pipeline config.
"""
import ConfigParser
import copy

import os
from ConfigParser import SafeConfigParser, RawConfigParser

import sys
from cStringIO import StringIO
from operator import itemgetter

from pimlico import PIMLICO_ROOT, PROJECT_ROOT, OUTPUT_DIR
from pimlico.core.dependencies.base import LegacyModuleDependencies, LegacyDatatypeDependencies
from pimlico.core.modules.options import str_to_bool, ModuleOptionParseError
from pimlico.utils.core import remove_duplicates
from pimlico.utils.format import title_box
from pimlico.utils.logging import get_console_logger

REQUIRED_LOCAL_CONFIG = ["short_term_store", "long_term_store"]


class PipelineConfig(object):
    """
    Main configuration for a pipeline, read in from a config file.

    Each section, except for `vars` and `pipeline`, defines a module instance in the pipeline. Some of these can
    be executed, others act as filters on the outputs of other modules, or input readers.

    **Special sections:**

    - vars:
        May contain any variable definitions, to be used later on in the pipeline. Further down, expressions like
        `%(varname)s` will be expanded into the value assigned to `varname` in the vars section.
    - pipeline:
        Main pipeline-wide configuration. The following options are required for every pipeline:

        * `name`: a single-word name for the pipeline, used to determine where files are stored
        * `release`: the release of Pimlico for which the config file was written. It is considered compatible with
          later minor versions of the same major release, but not with later major releases. Typically, a user
          receiving the pipeline config will get hold of an appropriate version of the Pimlico codebase to run it
          with.

        Other optional settings:

        * `python_path`: a path or paths, relative to the directory containing the config file, in which Python
          modules/packages used by the pipeline can be found. Typically, a config file is distributed with a
          directory of Python code providing extra modules, datatypes, etc. Multiple paths are separated by colons (:).

    **Special variable substitutions**

    Certain variable substitutions are always available, in addition to those defined in `vars` sections.

    - `pimlico_root`:
        Root directory of Pimlico, usually the directory `pimlico/` within the project directory.
    - `proejct_root`:
        Root directory of the whole project. Current assumed to always be the parent directory of `pimlico_root`.
    - `output_dir`:
        Path to output dir (usually `output` in Pimlico root).

    **Directives:**

    Certain special directives are processed when reading config files. They are lines that begin with `%%`, followed
    by the directive name and any arguments.

    - `variant`:
        Allows a line to be included only when loading a particular variant of a pipeline. The variant name is
        specified as part of the directive in the form: `variant:variant_name`. You may include the line in more
        than one variant by specifying multiple names, separated by commas (and no spaces). You can use the default
        variant "main", so that the line will be left out of other variants. The rest of the line, after the directive
        and variant name(s) is the content that will be included in those variants.
    - `novariant`:
        A line to be included only when not loading a variant of the pipeline. Equivalent to `variant:main`.
    - `include`:
        Include the entire contents of another file. The filename, specified relative to the config file in which the
        directive is found, is given after a space.
    - `abstract`:
        Marks a config file as being abstract. This means that Pimlico will not allow it to be loaded as a top-level
        config file, but only allow it to be included in another config file.
    - `copy`:
        Copies all config settings from another module, whose name is given as the sole argument. May be used multiple
        times in the same module and later copies will override earlier. Settings given explicitly in the module's
        config override any copied settings. The following settings are not copied: input(s), `filter`, `outputs`,
        `type`.

    **Multiple parameter values:**

    Sometimes you want to write a whole load of modules that are almost identical, varying in just one or two
    parameters. You can give a parameter multiple values by writing them separated by vertical bars (|). The module
    definition will be expanded to produce a separate module for each value, with all the other parameters being
    identical.

    You can even do this with multiple parameters of the same module and the expanded modules will cover all
    combinations of the parameter assignments.

    Each module will be given a distinct name, based on the varied parameters. If just one is varied, the names
    will be of the form `module_name{param_value}`. If multiple parameters are varied at once, the names will be
    `module_name{param_name0=param_value0~param_name1=param_value1~...)`.

    """
    def __init__(self, name, pipeline_config, local_config, raw_module_configs, module_order, filename=None,
                 variant="main", available_variants=[], log=None, all_filenames=None, module_docstrings={}):
        if log is None:
            log = get_console_logger("Pimlico")
        self.log = log

        self.available_variants = available_variants
        self.variant = variant
        self.module_docstrings = module_docstrings
        # Stores the module names in the order they were specified in the config file
        self.module_order = module_order
        self.local_config = local_config
        self.raw_module_configs = raw_module_configs
        self.pipeline_config = pipeline_config
        self.filename = filename
        self.all_filenames = all_filenames or [filename]
        self.name = name

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

        # Some modules need to know which of their (potential) outputs get used by other models when they're loaded
        # Since many modules need to load those they're dependent on while loading, this becomes cyclic!
        # Build a list of used outputs, before loading any modules
        self.used_outputs = {}
        for module_name in module_order:
            # Do minimal processing to get input connections: more thorough checks are done during instantiation
            for opt_name, opt_value in raw_module_configs[module_name].items():
                if opt_name == "input" or opt_name.startswith("input_"):
                    if "." in opt_value:
                        # Module name + output name
                        input_module, __, input_module_output = opt_value.partition(".")
                    else:
                        # Module name, with default output
                        input_module = opt_value
                        input_module_output = None
                    self.used_outputs.setdefault(input_module, set([])).add(input_module_output)

        # Never clear this. It's not really just a cache as such
        self._module_info_cache = {}
        self._module_schedule = None

        self._dependency_cache = None

    @property
    def modules(self):
        return self.module_order

    def __getitem__(self, item):
        return self.load_module_info(item)

    def __contains__(self, item):
        return item in self._module_info_cache or item in self.raw_module_configs

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

    def load_module_info(self, module_name):
        """
        Load the module metadata for a named module in the pipeline. Loads only this module's data
        and nothing more.

        :param module_name:
        :return:
        """
        # Cache the module info object so we can easily do repeated lookups without worrying about wasting time
        if module_name not in self._module_info_cache:
            from pimlico.core.modules.base import load_module_info
            from pimlico.core.modules.inputs import input_module_factory
            from pimlico.datatypes.base import load_datatype, DatatypeLoadError
            from pimlico.core.modules.map import DocumentMapModuleInfo
            from pimlico.core.modules.map.filter import wrap_module_info_as_filter

            if ":" in module_name:
                # Tried to load a multi-stage module's stage, but it doesn't exist
                main_module_name, __, stage_name = module_name.rpartition(":")
                if main_module_name in self:
                    raise PipelineStructureError("module '%s' does not have a stage named '%s'" %
                                                 (main_module_name, stage_name))
                else:
                    raise PipelineStructureError("undefined module '%s'" % main_module_name)
            elif module_name not in self.raw_module_configs:
                raise PipelineStructureError("undefined module '%s'" % module_name)
            module_config = self.raw_module_configs[module_name]

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

            # Allow document map types to be used as filters simply by specifying filter=T
            filter_type = str_to_bool(module_config.pop("filter", ""))

            # Work out what the previous module was, so that we can use it as a default connection
            try:
                module_index = self.module_order.index(module_name)
            except ValueError:
                module_index = 0
            previous_module_name = self.module_order[module_index-1] if module_index > 0 else None

            # Pass in all other options to the info constructor
            options_dict = dict(module_config)
            try:
                inputs, optional_outputs, options = module_info_class.process_config(
                    options_dict, module_name=module_name, previous_module_name=previous_module_name)
            except ModuleOptionParseError, e:
                raise PipelineConfigParseError("error in '%s' options: %s" % (module_name, e))

            # Instantiate the module info
            module_info = \
                module_info_class(module_name, self, inputs=inputs, options=options, optional_outputs=optional_outputs,
                                  docstring=self.module_docstrings.get(module_name, ""))

            # If we're loading as a filter, wrap the module info
            if filter_type:
                if not issubclass(module_info_class, DocumentMapModuleInfo):
                    raise PipelineStructureError("only document map module types can be treated as filters. Got option "
                                                 "filter=True for module %s" % module_name)
                module_info = wrap_module_info_as_filter(module_info)

            self._module_info_cache[module_name] = module_info
        return self._module_info_cache[module_name]

    def insert_module(self, module_info):
        """
        Usually, all modules in the pipeline are loaded, based on config, by this class. However, occasionally,
        we may want to make modules available as part of the pipeline from elsewhere. In particular, this is
        necessary when building multi-stage modules -- each stage is added (with special module name prefixes)
        into the main pipeline.

        """
        self._module_info_cache[module_info.module_name] = module_info

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
        from pimlico.core.modules.base import ModuleInfoLoadError

        if variant is None:
            variant = "main"

        if local_config is None:
            # Use the default locations for local config file
            # May want to add other locations here...
            local_config = [os.path.join(os.path.expanduser("~"), ".pimlico")]
        else:
            local_config = [local_config]

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
        local_config_data.update(override_local_config)

        for attr in REQUIRED_LOCAL_CONFIG:
            if attr not in local_config_data:
                raise PipelineConfigParseError("required attribute '%s' is not specified in local config" % attr)

        # Special vars are available for substitution in all options, including other vars
        special_vars = {
            "project_root": PROJECT_ROOT,
            "pimlico_root": PIMLICO_ROOT,
            "output_dir": OUTPUT_DIR,
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

        # Parameters and inputs can be given multiple values, separated by |s
        # In this case, we need to multiply out all the alternatives, to make multiple modules
        expanded_config_sections = []
        for section, section_config in config_sections:
            if any("|" in val for val in section_config.values()):
                # There are alternatives in this module: expand into multiple modules
                params_with_alternatives = {}
                fixed_params = {}
                for key, val in section_config.items():
                    if "|" in val:
                        # Split up the alternatives and allow space around the |s
                        params_with_alternatives[key] = [alt.strip() for alt in val.split("|")]
                    else:
                        fixed_params[key] = val
                # Generate all combinations of params that have alternatives
                alternative_configs = multiply_alternatives(params_with_alternatives.items())
                # Generate a name for each
                alternative_config_names = [
                    "%s{%s}" % (
                        section,
                        # If there's only 1 parameter that's varied, don't include the key in the name
                        params_set[0][1] if len(params_set) == 1
                            else "~".join("%s=%s" % (key, val) for (key, val) in params_set)
                    ) for params_set in alternative_configs
                ]
                # Add in fixed params to them all
                alternative_configs = [dict(params_set, **copy.deepcopy(fixed_params))
                                       for params_set in alternative_configs]
                expanded_config_sections.extend(zip(alternative_config_names, alternative_configs))
            else:
                # No alternatives
                expanded_config_sections.append((section, section_config))
        config_sections = expanded_config_sections
        config_section_dict = dict(expanded_config_sections)

        module_order = [section for section, config in config_sections if section != "pipeline"]

        # All other sections of the config describe a module instance
        # Don't do anything to the options just yet: they will be parsed and checked when the module info is created
        raw_module_options = dict([
            (
                section,
                # Perform our own version of interpolation here, substituting values from the vars section into others
                dict([(key, var_substitute(val, vars)) for (key, val) in config_section_dict[section].items()])
            ) for section in module_order
        ])

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

        # Do no further checking or processing at this stage: just keep raw dictionaries for the time being
        pipeline = PipelineConfig(
            name, pipeline_config, local_config_data, raw_module_options, module_order,
            filename=filename, variant=variant, available_variants=list(sorted(available_variants)),
            all_filenames=all_filenames, module_docstrings=section_docstrings,
        )

        # Now that we've got the pipeline instance prepared, load all the module info instances, so they're cached
        for module_name in module_order:
            try:
                pipeline.load_module_info(module_name)
            except ModuleInfoLoadError, e:
                raise PipelineConfigParseError("error loading module metadata for module '%s': %s" % (module_name, e))

        try:
            # Run all type-checking straight away so we know this is a valid pipeline
            check_pipeline(pipeline)
        except PipelineCheckError, e:
            raise PipelineConfigParseError("pipeline loaded, but failed checks: %s" % e, cause=e)

        return pipeline

    def find_data_path(self, path, default=None):
        """
        Given a path to a data dir/file relative to a data store, tries taking it relative to various store base
        dirs. If it exists in a store, that absolute path is returned. If it exists in no store, return None.

        The stores searched are the long-term store and the short-term store, though in the future more valid data
        storage locations may be added.

        :param path: path to data, relative to store base
        :param default: usually, return None if no data is found. If default="short", return path relative to
         short-term store in this case. If default="long", long-term store.
        :return: absolute path to data, or None if not found in any store
        """
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
    def __init__(self, *args, **kwargs):
        self.cause = kwargs.pop("cause", None)
        super(PipelineConfigParseError, self).__init__(*args, **kwargs)


class PipelineStructureError(Exception):
    pass


def preprocess_config_file(filename, variant="main", initial_vars={}):
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
    # Build a mapping representing module dependencies
    dep_map = dict(
        (module_name, pipeline.load_module_info(module_name).dependencies) for module_name in pipeline.modules
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
    Checks a pipeline over for metadata errors, cycles and other problems.
    Called every time a pipeline is loaded, to check the whole pipeline's metadata is in order.

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


def get_dependencies(pipeline, modules):
    """
    Get a list of software dependencies required by the subset of modules given.

    :param pipeline:
    :param modules: list of modules to check. If None, checks all modules
    """
    if modules is None:
        modules = pipeline.module_names

    # Add to the list of modules any that will be executed along with the specified ones
    modules = remove_duplicates(
        [mod.module_name for module_name in modules for mod in pipeline[module_name].get_all_executed_modules()]
    )

    dependencies = []
    for module_name in modules:
        module = pipeline[module_name]
        # Get any software dependencies for this module
        dependencies.extend(module.get_software_dependencies())
        # Also get dependencies of the input datatypes
        dependencies.extend(module.get_input_software_dependencies())

        ### These legacy wrappers will be removed later ###
        # Also wrap the module in order to check any dependencies specified in the old style, using
        #  check_runtime_dependencies()
        dependencies.append(LegacyModuleDependencies(module))
        # Do the same thing with the input datatypes
        for input_name in module.inputs.keys():
            for input in module.get_input(input_name, always_list=True):
                dependencies.append(LegacyDatatypeDependencies(input))

    # We may want to do something cleverer to remove duplicate dependencies, but at lest remove any duplicates
    #  of exactly the same object
    dependencies = remove_duplicates(dependencies, lambda x: id(x))
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


class PipelineCheckError(Exception):
    def __init__(self, cause, *args, **kwargs):
        super(PipelineCheckError, self).__init__(*args, **kwargs)
        self.cause = cause
