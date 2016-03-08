import argparse
import sys
from pimlico.core.config import PipelineConfig, PipelineConfigParseError, check_for_cycles, PipelineStructureError
from pimlico.core.modules.base import ModuleInfoLoadError

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load a Pimlico pipeline from config files and check it over")
    parser.add_argument("pipeline_config", help="Config file to load a pipeline from")
    opts = parser.parse_args()

    # Read in the pipeline config from the given file
    try:
        pipeline = PipelineConfig.load(opts.pipeline_config)
    except PipelineConfigParseError, e:
        print >>sys.stderr, "Error reading pipeline config: %s" % e
        sys.exit(1)

    # Load all the modules' metadata
    # This makes sure none of the modules have trouble loading
    for name in pipeline.modules:
        try:
            pipeline.load_module_info(name)
        except ModuleInfoLoadError, e:
            print "Error loading module %s: %s" % (name, e)
            sys.exit(1)
    print "All module metadata loaded successfully"

    # Check the pipeline for cycles
    # This will raise an exception if a cycle is found
    try:
        check_for_cycles(pipeline)
    except PipelineStructureError, e:
        print "Cycle check failed: %s" % e
        sys.exit(1)
    print "No cycles found"

    # Check the types of all the output->input connections
    try:
        for module in pipeline.modules:
            mod = pipeline[module]
            mod.typecheck_inputs()
    except PipelineStructureError, e:
        print "Input typechecking failed: %s" % e
        sys.exit(1)
    print "All inputs pass type checks"
