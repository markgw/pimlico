"""
Reading of various types of config files, in particular a pipeline config.
"""
import ConfigParser
import os
from ConfigParser import SafeConfigParser, RawConfigParser

import sys
from cStringIO import StringIO

REQUIRED_LOCAL_CONFIG = ["short_term_store", "long_term_store"]


class PipelineConfig(object):
    """
    Main configuration for a pipeline, usually read in from a config file.

    Each section, except for the special ones below, defines a module in the pipeline. Some of these can
    be executed, others act as filters on the outputs of other modules, or input readers.

    Special sections
    ================

    - vars:
        May contain any variable definitions, to be used later on in the pipeline. Further down, expressions like
        `%(varname)s` will be expanded into the value assigned to `varname` in the vars section.
    - pipeline:
        Main pipeline-wide configuration. The following options are required for every pipeline:
        - name: a single-word name for the pipeline, used to determine where files are stored
        - release: the release of Pimlico for which the config file was written. It is considered compatible with
            later minor versions of the same major release, but not with later major releases. Typically, a user
            receiving the pipeline config will get hold of an appropriate version of the Pimlico codebase to run it
            with.
        Other optional settings:
        - python_path: a path or paths, relative to the directory containing the config file, in which Python
            modules/packages used by the pipeline can be found. Typically, a config file is distributed with a
            directory of Python code providing extra modules, datatypes, etc. Multiple paths are separated by `:`s

    Directives
    ==========
    Certain special directives are processed when reading config files. They are lines that begin with "%%", followed
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

    """
    def __init__(self, pipeline_config, local_config, raw_module_configs, module_order, filename=None,
                 variant="main", available_variants=[]):
        self.available_variants = available_variants
        self.variant = variant
        # Stores the module names in the order they were specified in the config file
        self.module_order = module_order
        self.local_config = local_config
        self.raw_module_configs = raw_module_configs
        self.pipeline_config = pipeline_config
        self.filename = filename

        # Process configs to get out the core things we need
        if "name" not in self.pipeline_config:
            raise PipelineConfigParseError("pipeline name must be specified as 'name' attribute in pipeline section")
        self.name = self.pipeline_config["name"]
        # Check that this pipeline is compatible with the Pimlico version being used
        if "release" not in self.pipeline_config:
            raise PipelineConfigParseError("Pimlico release version must be specified as 'release' attribute in "
                                           "pipeline section")
        check_release(self.pipeline_config["release"])

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

        self._module_info_cache = {}
        self._module_schedule = None

        # Now that we've got the pipeline instance prepared, load all the module info instances, so they've cached
        for module_name in module_order:
            self.load_module_info(module_name)

    @property
    def modules(self):
        return self.module_order

    def __getitem__(self, item):
        return self.load_module_info(item)

    def load_module_info(self, module_name):
        """
        Load the module metadata for a named module in the pipeline. Loads only this module's data
        and nothing more.

        :param module_name:
        :return:
        """
        # Cache the module info object so we can easily do repreated lookups without worrying about wasting time
        if module_name not in self._module_info_cache:
            from pimlico.core.modules.base import load_module_info
            from pimlico.core.modules.inputs import input_module_factory
            from pimlico.datatypes.base import load_datatype, DatatypeLoadError

            if module_name not in self.raw_module_configs:
                raise PipelineStructureError("undefined module '%s'" % module_name)
            module_config = self.raw_module_configs[module_name]

            # Load the module info class for the declared type of the module in the config
            if "type" not in module_config:
                raise PipelineConfigParseError("module %s does not specify a type" % module_name)
            try:
                # First see if this is a datatype
                datatype_class = load_datatype(module_config["type"])
                # Get an input module info class for this datatype
                module_info_class = input_module_factory(datatype_class)
            except DatatypeLoadError:
                # Not a datatype
                module_info_class = load_module_info(module_config["type"])

            # Pass in all other options to the info constructor
            options_dict = dict(module_config)
            inputs, optional_outputs, options = module_info_class.process_config(options_dict)

            # Instantiate the module info
            self._module_info_cache[module_name] = \
                module_info_class(module_name, self, inputs=inputs, options=options, optional_outputs=optional_outputs)
        return self._module_info_cache[module_name]

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
    def load(filename, local_config=None, variant="main"):
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

        for attr in REQUIRED_LOCAL_CONFIG:
            if attr not in local_config_data:
                raise PipelineConfigParseError("required attribute '%s' is not specified in local config" % attr)

        # Perform pre-processing of config file to replace includes, etc
        config_text, available_variants = preprocess_config_file(os.path.abspath(filename), variant=variant)
        # If we were asked to load a particular variant, check it's in the list of available variants
        if variant != "main" and variant not in available_variants:
            raise PipelineConfigParseError("could not load pipeline variant '%s': it is not declared anywhere in the "
                                           "config file")
        text_buffer = StringIO(config_text)

        # Parse the config file text
        config_parser = RawConfigParser()
        try:
            config_parser.readfp(text_buffer)

            # Check for the special overall pipeline config section "pipeline"
            if not config_parser.has_section("pipeline"):
                raise PipelineConfigParseError("no 'pipeline' section found in config: must be supplied to give basic "
                                               "pipeline configuration")
            pipeline_config = dict(config_parser.items("pipeline"))

            # Also check for a "vars" section, which allows variables to be defined and substituted into other sections
            if config_parser.has_section("vars"):
                vars = dict(config_parser.items("vars"))
            else:
                vars = {}

            module_order = [section for section in config_parser.sections() if section not in ("pipeline", "vars")]

            # All other sections of the config describe a module instance
            # Don't do anything to the options just yet: they will be parsed and checked when the module info is created
            raw_module_options = dict([
                (section,
                 # Perform our own version of interpolation here,
                 # just substituting values from the vars section into others
                 dict([(key, var_substitute(val, vars)) for (key, val) in config_parser.items(section)]))
                for section in module_order
            ])
        except ConfigParser.Error, e:
            raise PipelineConfigParseError("could not parse config file. %s" % e)

        # Do no further checking or processing at this stage: just keep raw dictionaries for the time being
        return PipelineConfig(pipeline_config, local_config_data, raw_module_options, module_order,
                              filename=filename, variant=variant, available_variants=list(sorted(available_variants)))


def var_substitute(option_val, vars):
    try:
        return option_val % vars
    except KeyError, e:
        raise PipelineConfigParseError("error making substitutions in %s: var %s not specified" % (option_val, e))
    except BaseException, e:
        raise PipelineConfigParseError("error (%s) making substitutions in %s: %s" % (type(e).__name__, option_val, e))


class PipelineConfigParseError(Exception):
    pass


class PipelineStructureError(Exception):
    pass


def preprocess_config_file(filename, variant="main"):
    # Read in the file
    config_lines = []
    available_variants = set([])
    with open(filename, "r") as f:
        # ConfigParser can read directly from a file, but we need to pre-process the text
        for line in f:
            if line.startswith("%% "):
                # Directive: process this now
                directive, __, rest = line[3:].partition(" ")
                if directive.lower() == "novariant":
                    # Include this line only if loading the main variant
                    if variant == "main":
                        config_lines.append(rest.lstrip())
                elif directive.lower().startswith("variant:"):
                    variant_cond = directive[8:]
                    # Line conditional on a specific variant: include only if we're loading that variant
                    if variant_cond == variant:
                        config_lines.append(rest.lstrip())
                    # Keep a list of all available variants
                    available_variants.add(variant_cond)
                elif directive == "include":
                    # Include another file, given relative to this one
                    include_filename = os.path.abspath(os.path.join(os.path.dirname(filename), rest.strip("\n ")))
                    # Run preprocessing over that file too, so we can have embedded includes, etc
                    incl_text, incl_variants = preprocess_config_file(include_filename, variant=variant)
                    config_lines.append(incl_text)
                    available_variants.update(incl_variants)
                else:
                    raise PipelineConfigParseError("unknown directive '%s' used in config file" % directive)
            else:
                config_lines.append(line)
    return "".join(config_lines), available_variants


def check_for_cycles(pipeline):
    # Build a mapping representing module dependencies
    dep_map = dict(
        (module_name, pipeline.load_module_info(module_name).dependencies) for module_name in pipeline.modules
    )

    def _search(node, check_for):
        if len(dep_map[node]) == 0:
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
    given_major_release, __, given_minor_release = release_str.partition(".")
    current_major_release, given_major_release = int(current_major_release), int(given_major_release)

    if current_major_release < given_major_release:
        raise PipelineStructureError("config file was written for a later version of Pimlico than the one you're "
                                     "running. You need to update Pimlico (or check out a later release), as there "
                                     "could be backwards-incompatible changes between major versions. Running version "
                                     "%s, required version %s" % (__version__, release_str))
    elif current_major_release > given_major_release:
        raise PipelineStructureError("config file was written for an earlier version of Pimlico than the one you're "
                                     "running. You need to check out an earlier release, as the behaviour of Pimlico "
                                     "could be very different to when the config file was written. Running version "
                                     "%s, required version %s" % (__version__, release_str))
    # Right major version
    # Check we're not running an earlier minor version
    remaining_current = current_minor_release
    remaining_given = given_minor_release
    while len(remaining_given):
        if len(remaining_current) == 0:
            # Given version has the same prefix, but specifies more subversions, so is a later release
            raise PipelineStructureError("config file was written for a later (minor) version of Pimlico than the "
                                         "one you're running. You need to use >= v%s to run this config "
                                         "file (and not > %s). Currently using %s" %
                                         (release_str, given_major_release, __version__))
        current_part, __, remaining_current = remaining_current.partition(".")
        given_part, __, remaining_given = remaining_given.partition(".")
        if int(current_part) > int(given_part):
            # Using a higher minor version than required: stop checking
            break
        elif int(current_part) < int(given_part):
            raise PipelineStructureError("config file was written for a later (minor) version of Pimlico than the "
                                         "one you're running. You need to use >= v%s to run this config "
                                         "file (and not > %s). Currently using %s" %
                                         (release_str, given_major_release, __version__))
        # Otherwise using same version at this level: go down to next level and check
