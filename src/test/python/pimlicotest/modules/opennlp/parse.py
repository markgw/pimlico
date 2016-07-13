import unittest

from pimlico.core.config import PipelineConfig
from pimlico.core.dependencies.base import install_dependencies
from pimlico.core.modules.execute import execute_module
from pimlicotest import example_path


class ParsePipeline(unittest.TestCase):
    def setUp(self):
        # Load the pipeline
        self.pipeline = PipelineConfig.load(example_path("opennlp_parse", "opennlp_parse.conf"))

    def test_parse_pipeline(self):
        # Check dependencies are installed
        install_dependencies(self.pipeline)
        self.pipeline.reset_all_modules()
        # TODO This relies on having models available, but it's not currently possible to install them programmatically
        execute_module(self.pipeline, "input-text")
        execute_module(self.pipeline, "tokenize")
        execute_module(self.pipeline, "pos-tag")
        # TODO We don't actually parse at the moment. Add to the pipeline

        # Restore to start state
        self.pipeline.reset_all_modules()
