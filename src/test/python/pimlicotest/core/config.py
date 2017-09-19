import tempfile
import unittest
from pimlicotest import example_path


class PipelineConfigTest(unittest.TestCase):
    def setUp(self):
        # Get a basic local config file so Pimlico doesn't go looking for one on the system
        self.local_conf_path = example_path("tests_local_config")
        # Create a temporary directory to use as our storage location
        self.storage_dir = tempfile.mkdtemp()
        # Override the local config values that should point to this path
        self.override_local_config = {
            "long_term_store": self.storage_dir,
            "short_term_store": self.storage_dir,
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.storage_dir)


class TestEmptyPipelineLoading(PipelineConfigTest):
    """
    Load a pipeline config file that doesn't contain any modules
    """
    def test_load(self):
        from pimlico.core.config import PipelineConfig

        # Load a config file
        conf_path = example_path("empty.conf")
        pipeline = PipelineConfig.load(conf_path,
                                       local_config=self.local_conf_path,
                                       override_local_config=self.override_local_config)


class TestEmptyPipelineCreation(PipelineConfigTest):
    """
    Create an empty pipeline programmatically.

    """
    def test_load(self):
        from pimlico.core.config import PipelineConfig
        pipeline = PipelineConfig.empty(local_config=self.local_conf_path,
                                        override_local_config=self.override_local_config)


if __name__ == "__main__":
    unittest.main()
