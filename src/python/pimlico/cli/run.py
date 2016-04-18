import argparse
import os

import sys
from operator import itemgetter

from pimlico.cli.check import check_cmd
from pimlico.core.config import PipelineConfig, PipelineConfigParseError
from pimlico.core.modules.execute import execute_module, ModuleExecutionError
from pimlico.utils.filesystem import copy_dir_with_progress


def status_cmd(pipeline, opts):
    # Try deriving a schedule
    print "Module execution schedule with statuses"
    for i, module_name in enumerate(pipeline.get_module_schedule(), start=1):
        module = pipeline[module_name]
        print " %d. %s" % (i, module_name)
        # Check module status (has it been run?)
        print "       status: %s" % module.status
        # Check status of each input datatypes
        for input_name in module.input_names:
            print "       input %s: %s" % (input_name, "ready" if module.input_ready(input_name) else "not ready")
        print "       outputs: %s" % ", ".join(module.output_names)


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


def reset_module(pipeline, opts):
    if opts.module_name == "all":
        # Reset every module, one by one
        module_names = pipeline.modules
    else:
        module_names = opts.module_name.split(",")
    for module_name in module_names:
        print "Resetting execution state of module %s" % module_name
        module = pipeline[module_name]
        module.reset_execution()


def list_variants(pipeline, opts):
    # Main is the default pipeline config and is always available (but not included in this list)
    variants = ["main"] + pipeline.available_variants
    print "Available pipeline variants: %s" % ", ".join(variants)
    print "Select one using the --variant option"


def short_to_long(pipeline, opts):
    module_name = opts.module_name
    # Get the path within the stores
    module_path = pipeline[module_name].get_module_output_dir()
    # Work out where it lives in the short-term and long-term stores
    short_term_dir = os.path.join(pipeline.short_term_store, module_path)
    long_term_dir = os.path.join(pipeline.long_term_store, module_path)
    copy_dir_with_progress(short_term_dir, long_term_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Main command line interface to PiMLiCo")
    parser.add_argument("pipeline_config", help="Config file to load a pipeline from")
    parser.add_argument("--debug", "-d", help="Output verbose debugging info", action="store_true")
    parser.add_argument("--variant", "-v", help="Load a particular variant of a pipeline. For a list of available "
                                                "variants, use the 'variants' command", default="main")
    parser.add_argument("--override-local-config", "--local", "-l",
                        help="Override a parameter set in the local config files (usually ~/.pimlico.conf). For just "
                             "this execution. Specify as param=value. Use this option multiple times to override "
                             "more than one parameter", action="append")
    parser.add_argument("--processes", "-p",
                        help="Set the number of processes to use for this run, where parallelization is available. "
                             "Overrides the local config setting. Equivalent to '-l processes=P'", type=int)
    subparsers = parser.add_subparsers(help="Select a sub-command")

    check = subparsers.add_parser("check",
                                  help="Test a pipeline config to check that it can be parsed and is valid. It is "
                                       "recommended that you run this before attempting to execute any modules")
    check.set_defaults(func=check_cmd)
    check.add_argument("modules", nargs="*",
                       help="Check runtime dependencies for named modules. By default, these are not all checked, as "
                            "you might be happy with them not all being satisfied at once")

    status = subparsers.add_parser("status", help="Output a module execution schedule for the pipeline and execution "
                                                  "status for every module")
    status.set_defaults(func=status_cmd)

    run = subparsers.add_parser("run", help="Execute an individual pipeline module")
    run.set_defaults(func=run_cmd)
    run.add_argument("module_name", help="The name of the module to run")
    run.add_argument("--force-rerun", "-f", action="store_true",
                     help="Force running the module, even if it's already been run to completion")

    variants = subparsers.add_parser("variants", help="List the available variants of a pipeline config")
    variants.set_defaults(func=list_variants)

    reset = subparsers.add_parser("reset",
                                  help="Delete any output from the given module and restore it to unexecuted state")
    reset.set_defaults(func=reset_module)
    reset.add_argument("module_name", help="The name of the module to reset, or multiple separated by commas, or "
                                           "'all' to reset the whole pipeline")

    reset = subparsers.add_parser("longstore",
                                  help="Move a particular module's output from the short-term store to the long-term "
                                       "store. It will still be found here by input readers. You might want to do "
                                       "this if your long-term store is bigger, to keep down the short-term store size")
    reset.set_defaults(func=short_to_long)
    reset.add_argument("module_name", help="The name of the module whose output to move")

    opts = parser.parse_args()

    if opts.override_local_config is not None:
        override_local = dict(
            itemgetter(0, 2)(param.partition("=")) for param in opts.override_local_config
        )
    else:
        override_local = {}
    if opts.processes is not None:
        # Override the processes local config setting
        override_local["processes"] = opts.processes

    # Read in the pipeline config from the given file
    try:
        pipeline = PipelineConfig.load(opts.pipeline_config, variant=opts.variant,
                                       override_local_config=override_local)
    except PipelineConfigParseError, e:
        print >>sys.stderr, "Error reading pipeline config: %s" % e
        sys.exit(1)
    # Run the function corresponding to the subcommand
    opts.func(pipeline, opts)
