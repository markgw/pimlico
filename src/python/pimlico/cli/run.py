import argparse
import sys
from pimlico.core.config import PipelineConfig, PipelineConfigParseError

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Main command line interface to PiMLiCo")
    parser.add_argument("pipeline_config", help="Config file to load a pipeline from")
    opts = parser.parse_args()

    # Read in the pipeline config from the given file
    try:
        config = PipelineConfig.load(opts.pipeline_config)
    except PipelineConfigParseError, e:
        print >>sys.stderr, "Error reading pipeline config: %s" % e
        sys.exit(1)
