"""
Reading of various types of config files, in particular a pipeline config.
"""
from ConfigParser import SafeConfigParser
from cStringIO import StringIO
from pimlico.core.module import load_module_info


class PipelineConfig(object):
    def __init__(self, pipeline_config, raw_module_configs, filename=None):
        self.raw_module_configs = raw_module_configs
        self.pipeline_config = pipeline_config
        self.filename = filename

    @staticmethod
    def load(filename):
        # TODO Perform pre-processing of config file to replace variables, includes, etc
        with open(filename, "r") as f:
            # ConfigParser can read directly from a file, but we need to pre-process the text
            config_text = f.read()
        text_buffer = StringIO(config_text)

        # Parse the config file text
        config_parser = SafeConfigParser()
        config_parser.read(text_buffer)

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
        return PipelineConfig(pipeline_config, raw_module_options, filename=filename)

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
