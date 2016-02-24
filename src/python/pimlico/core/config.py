"""
Reading of various types of config files, in particular a pipeline config.
"""
from ConfigParser import SafeConfigParser
from cStringIO import StringIO


class PipelineConfig(object):
    def __init__(self, root_filename=None):
        self.root_filename = root_filename

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
        pipeline_config = config_parser.items("pipeline")
        # TODO Remove
        print pipeline_config

        # All other sections of the config describe a module instance
        module_options = [config_parser.items(section) for section in config_parser.sections() if section != "pipeline"]
        # TODO Remove
        print module_options


class PipelineConfigParseError(Exception):
    pass
