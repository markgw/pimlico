import argparse
import sys
from pimlico.cli.check import check_cmd
from pimlico.core.config import PipelineConfig, PipelineConfigParseError
from pimlico.core.modules.execute import execute_module, ModuleExecutionError


def schedule_cmd(pipeline, opts):
    # Try deriving a schedule
    print "Module execution schedule"
    for i, module_name in enumerate(pipeline.get_module_schedule(), start=1):
        module = pipeline[module_name]
        print " %d. %s" % (i, module_name)
        # Check module status (has it been run?)
        print "       status: %s" % module.status
        # Check status of each input datatypes
        for input_name in module.input_names:
            print "       input %s: %s" % (input_name, "ready" if module.input_ready(input_name) else "not ready")


def run_cmd(pipeline, opts):
    try:
        execute_module(pipeline, opts.module_name, force_rerun=opts.force_rerun, debug=opts.debug)
    except ModuleExecutionError, e:
        print >>sys.stderr, "Error executing module '%s': %s" % (opts.module_name, e)
    except KeyboardInterrupt:
        print >>sys.stderr, "Exiting before execution completed due to user interrupt"
        # Raise the exception so we see the full stack trace
        if opts.debug:
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Main command line interface to PiMLiCo")
    parser.add_argument("pipeline_config", help="Config file to load a pipeline from")
    parser.add_argument("--debug", help="Output verbose debugging info", action="store_true")
    subparsers = parser.add_subparsers(help="Select a sub-command")

    check = subparsers.add_parser("check",
                                  help="Test a pipeline config to check that it can be parsed and is valid. It is "
                                       "recommended that you run this before attempting to execute any modules")
    check.set_defaults(func=check_cmd)
    check.add_argument("--runtime", action="store_true",
                       help="Check runtime dependencies for all modules. By default, these are not check as you might "
                            "be happy with them not all being satisfied at once")

    schedule = subparsers.add_parser("schedule", help="Output a module execution schedule for the pipeline")
    schedule.set_defaults(func=schedule_cmd)

    run = subparsers.add_parser("run", help="Execute an individual pipeline module")
    run.set_defaults(func=run_cmd)
    run.add_argument("module_name", help="The name of the module to run")
    run.add_argument("--force-rerun", "-f", action="store_true",
                     help="Force running the module, even if it's already been run to completion")

    opts = parser.parse_args()

    # Read in the pipeline config from the given file
    try:
        pipeline = PipelineConfig.load(opts.pipeline_config)
    except PipelineConfigParseError, e:
        print >>sys.stderr, "Error reading pipeline config: %s" % e
        sys.exit(1)
    # Run the function corresponding to the subcommand
    opts.func(pipeline, opts)
