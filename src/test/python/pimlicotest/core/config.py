import unittest
from pimlicotest import example_path
from pimlico.core.config import PipelineConfig


class TestEmptyPipelineLoading(unittest.TestCase):
    def test_load(self):
        # Load a config file
        conf_path = example_path("empty.conf")
        pipeline = PipelineConfig.load(conf_path)


if __name__ == "__main__":
    unittest.main()
