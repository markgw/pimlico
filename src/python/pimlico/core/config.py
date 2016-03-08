"""
Reading of various types of config files, in particular a pipeline config.
"""
from ConfigParser import SafeConfigParser
from cStringIO import StringIO
import os

REQUIRED_LOCAL_CONFIG = ["short_term_store", "long_term_store"]


class PipelineConfig(object):
    def __init__(self, pipeline_config, local_config, raw_module_configs, filename=None):
        self.local_config = local_config
        self.raw_module_configs = raw_module_configs
        self.pipeline_config = pipeline_config
        self.filename = filename

        # Process configs to get out the core things we need
        if "name" not in self.pipeline_config:
            raise PipelineConfigParseError("pipeline name must be specified as 'name' attribute in pipeline section")
        self.name = self.pipeline_config["name"]
        self.long_term_store = self.local_config["long_term_store"]
        self.short_term_store = self.local_config["short_term_store"]

        self._module_info_cache = {}

    @property
    def modules(self):
        return self.raw_module_configs.keys()

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

            if module_name not in self.raw_module_configs:
                raise PipelineStructureError("undefined module '%s'" % module_name)
            module_config = self.raw_module_configs[module_name]

            # Load the module info class for the declared type of the module in the config
            if "type" not in module_config:
                raise PipelineConfigParseError("module %s does not specify a type" % module_name)
            module_info_class = load_module_info(module_config["type"])

            # Pass in all other options to the info constructor
            options_dict = dict(module_config)
            inputs, options = module_info_class.process_config(options_dict)

            # Instantiate the module info
            self._module_info_cache[module_name] = \
                module_info_class(module_name, self, inputs=inputs, options=options_dict)
        return self._module_info_cache[module_name]

    @staticmethod
    def load(filename, local_config=None):
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

        # TODO Perform pre-processing of config file to replace variables, includes, etc
        with open(filename, "r") as f:
            # ConfigParser can read directly from a file, but we need to pre-process the text
            config_text = f.read()
        text_buffer = StringIO(config_text)

        # Parse the config file text
        config_parser = SafeConfigParser()
        config_parser.readfp(text_buffer)

        # Check for the special overall pipeline config section "pipeline"
        if not config_parser.has_section("pipeline"):
            raise PipelineConfigParseError("no 'pipeline' section found in config: must be supplied to give basic "
                                           "pipeline configuration")
        pipeline_config = dict(config_parser.items("pipeline"))

        # All other sections of the config describe a module instance
        # Don't do anything to the options just yet: they will be parsed and checked when the module info is created
        raw_module_options = dict([
            (section, dict(config_parser.items(section)))
            for section in config_parser.sections() if section != "pipeline"
        ])
        # Do no further checking or processing at this stage: just keep raw dictionaries for the time being
        return PipelineConfig(pipeline_config, local_config_data, raw_module_options, filename=filename)

        # module_types = []
        # for name, opts in raw_module_options:
        #     if "type" not in opts:
        #         raise PipelineConfigParseError("module '%s' has no 'type' attribute" % name)
        #     module_types.append(opts.pop("type"))
        #
        # # Load a ModuleInfo class to get metadata for each module defined
        # module_classes = [load_module_info(module_type) for module_type in module_types]


class PipelineConfigParseError(Exception):
    pass


class PipelineStructureError(Exception):
    pass


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
