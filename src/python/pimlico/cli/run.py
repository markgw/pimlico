# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
from pimlico.cli.util import module_number_to_name
from pimlico.utils.core import remove_duplicates
from pimlico.utils.logging import get_console_logger
from pimlico.utils.system import set_proc_title

if __name__ == "__main__":
    from pimlico import install_core_dependencies
    install_core_dependencies()

import argparse
import os
import sys
from operator import itemgetter
from traceback import print_exc, format_exception_only

from pimlico.cli.check import check_cmd, install_cmd, deps_cmd
from pimlico.cli.status import status_cmd
from pimlico.core.config import PipelineConfig, PipelineConfigParseError
from pimlico.core.modules.base import ModuleInfoLoadError
from pimlico.core.modules.execute import ModuleExecutionError, check_and_execute_modules
from pimlico.utils.filesystem import copy_dir_with_progress
from .shell.runner import shell_cmd
from pimlico.core.modules.multistage import MultistageModuleInfo


def run_cmd(pipeline, opts):
    debug = opts.debug
    log = get_console_logger("Pimlico", debug=debug)

    if opts.modules is None or len(opts.modules) == 0:
        # No module name given: default to next one that's ready to run
        modules = [(module_name, pipeline[module_name]) for module_name in pipeline.modules]
        ready_modules = [module_name for (module_name, module) in modules
                         if module.module_executable and not module.is_locked()
                         and module.status != "COMPLETE" and module.all_inputs_ready()]
        if len(ready_modules) == 0:
            print >>sys.stderr, "No modules not already completed have all their inputs ready: no module name to " \
                                "default to"
            sys.exit(1)
        else:
            module_specs = [ready_modules[0]]
            log.info("No module name specified. Defaulting to next unexecuted, ready module: '%s'" % module_spec)
    else:
        module_specs = opts.modules
        for module_spec in module_specs:
            # In the case of a multi-stage module allow a list to be output of available stages
            module_name, __, stage_name = module_spec.rpartition(":")
            if stage_name in ["?", "help"]:
                # Just output stage names and exit
                module = pipeline[module_name]
                if not isinstance(module, MultistageModuleInfo):
                    print "%s is not a multi-stage module" % module_name
                    sys.exit(1)
                print "Module stages: %s" % ", ".join(stage.name for stage in module.stages)
                sys.exit(0)

    pipeline_name = "'%s'" % pipeline.name if pipeline.variant == "main" else \
        "'%s' (variant '%s')" % (pipeline.name, pipeline.variant)
    log.info("Using pipeline %s" % pipeline_name)

    try:
        check_and_execute_modules(pipeline, module_specs, force_rerun=opts.force_rerun, debug=debug, log=log)
    except ModuleInfoLoadError, e:
        if debug:
            print_exc()
            if e.cause is not None:
                print >>sys.stderr, "Caused by: %s" % "".join(format_exception_only(type(e.cause), e.cause)),
        # See whether the problem came from a specific module
        module_name = getattr(e, "module_name", None)
        if module_name is not None:
            print >>sys.stderr, "Error loading module '%s': %s" % (module_name, e)
    except ModuleExecutionError, e:
        if debug:
            print >>sys.stderr, "Top-level error"
            print >>sys.stderr, "---------------"
            print_exc()
            print_execution_error(e)
        # See whether the problem came from a specific module
        module_name = getattr(e, "module_name", None)
        if module_name is not None:
            print >>sys.stderr, "Error executing module '%s': %s" % (module_spec, e)
    except KeyboardInterrupt:
        print >>sys.stderr, "Exiting before execution completed due to user interrupt"
        # Raise the exception so we see the full stack trace
        if debug:
            raise


def print_execution_error(error):
    print >>sys.stderr, "\nDetails of error"
    print >>sys.stderr,   "----------------"
    print >>sys.stderr, "".join(format_exception_only(type(error), error)).strip("\n")
    if hasattr(error, "debugging_info") and error.debugging_info is not None:
        # Extra debugging information was provided by the exception
        print >>sys.stderr, "\n## Further debugging info ##"
        print >>sys.stderr, error.debugging_info.strip("\n")
    if hasattr(error, "cause") and error.cause is not None:
        # Recursively print any debugging info on the cause exception
        print_execution_error(error.cause)


def reset_module(pipeline, opts):
    if opts.module_name == "all":
        # Reset every module, one by one
        print "Resetting execution state of all modules"
        pipeline.reset_all_modules()
    else:
        module_names = opts.module_name.split(",")
        if opts.no_deps:
            dependent_modules = []
        else:
            # Check for modules that depend on these ones: they should also be reset, since their input data will be rebuilt
            dependent_modules = remove_duplicates(sum(
                (pipeline.get_dependent_modules(module_name, recurse=True) for module_name in module_names), []
            ))
            dependent_modules = [m for m in dependent_modules if m not in module_names]
            # Don't bother to include ones that haven't been executed anyway
            dependent_modules = [m for m in dependent_modules if pipeline[m].status != "UNEXECUTED"]
            if len(dependent_modules) > 0:
                # There are additional modules that we should reset along with these,
                # but check with the user in case they didn't intend that
                print "The following modules depend on %s. Their execution state will be reset too if you continue." % \
                      ", ".join(module_names)
                print "  %s" % ", ".join(dependent_modules)
                answer = raw_input("Do you want to continue? [y/N] ")
                if answer.lower() != "y":
                    print "Cancelled"
                    return

        for module_name in module_names + dependent_modules:
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


def unlock_cmd(pipeline, opts):
    module = pipeline[opts.module_name]
    if not module.is_locked():
        print "Module '%s' is not locked" % opts.module_name
    else:
        module.unlock()
        print "Module unlocked"


def browse_cmd_with_deps(*args):
    # When this is first imported, it checks that it has its dependencies
    from .browser.tool import browse_cmd
    return browse_cmd(*args)


def inputs_cmd(pipeline, opts):
    module_name = opts.module_name
    print "Input locations for module '%s'" % module_name
    module = pipeline[module_name]

    # Display info for each input to this module
    for input_name in module.input_names:
        print "\nInput '%s'" % input_name
        input_lst = module.get_input(input_name, always_list=True)
        input_connections = module.get_input_module_connection(input_name, always_list=True)
        multiple_inputs = len(input_lst) > 1
        if multiple_inputs:
            print "Multiple input sources: showing locations for all"

        for i, (input_datatype, (prev_module, prev_output_name, __)) in \
                enumerate(zip(input_lst, input_connections)):
            if multiple_inputs:
                print "## Input source %d ##" % i

            if input_datatype.data_ready():
                corpus_dir = input_datatype.absolute_base_dir
                if corpus_dir is None:
                    print "Data (%s) available, but no directory given: probably a filter datatype" % \
                          input_datatype.full_datatype_name()
                else:
                    print "Data (%s) available in:" % input_datatype.full_datatype_name()
                    print " - %s" % corpus_dir
            else:
                print "Data not available. Data will be found in any of the following locations:"
                # Get the relative dir within the Pimlico dir structures
                rel_path = prev_module.get_output_dir(prev_output_name)
                # Resolve this to all possible absolute dirs (usually two)
                abs_paths = remove_duplicates(pipeline.get_data_search_paths(rel_path))
                print "\n".join(" - %s" % pth for pth in abs_paths)


def output_cmd(pipeline, opts):
    module_name = opts.module_name
    module = pipeline[module_name]
    # Get the output dir for the module
    module_output_dir = module.get_module_output_dir(short_term_store=True)
    print "Output location for module '%s': %s" % (module_name, module_output_dir)


def visualize_cmd(pipeline, opts):
    from pimlico.core.visualize.status import build_graph_with_status
    build_graph_with_status(pipeline, all=opts.all)


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
    check.add_argument("--verbose", "-v", action="store_true",
                       help="Show details of why dependencies aren't available where possible")

    status = subparsers.add_parser("status", help="Output a module execution schedule for the pipeline and execution "
                                                  "status for every module")
    status.add_argument("module_name", nargs="?",
                        help="Optionally specify a module name (or number). More detailed status information will be "
                             "outut for this module. Alternatively, use this arg to limit the modules whose status "
                             "will be output to a range by specifying 'A...B', where A and B are module names or "
                             "numbers")
    status.add_argument("--all", "-a", action="store_true",
                        help="Show all modules defined in the pipeline, not just those that can be executed")
    status.add_argument("--history", "-i", action="store_true",
                        help="When a module name is given, even more detailed output is given, including the full "
                             "execution history of the module")
    status.set_defaults(func=status_cmd)

    visualize = subparsers.add_parser("visualize", help="Visualize the pipeline, with status information for modules")
    visualize.add_argument("--all", "-a", action="store_true",
                           help="Show all modules defined in the pipeline, not just those that can be executed")
    visualize.set_defaults(func=visualize_cmd)

    run = subparsers.add_parser("run", help="Execute an individual pipeline module, or a sequence")
    run.set_defaults(func=run_cmd)
    run.add_argument("modules", nargs="*",
                     help="The name (or number) of the module to run. To run a stage from a multi-stage "
                          "module, use 'module:stage'. Use 'status' command to see available modules. "
                          "Use 'module:?' or 'module:help' to list available stages. If not given, "
                          "defaults to next incomplete module that has all its inputs ready. You may give "
                          "multiple modules, in which case they will be executed in the order specified")
    run.add_argument("--force-rerun", "-f", action="store_true",
                     help="Force running the module(s), even if it's already been run to completion")

    variants = subparsers.add_parser("variants", help="List the available variants of a pipeline config")
    variants.set_defaults(func=list_variants)

    reset = subparsers.add_parser("reset",
                                  help="Delete any output from the given module and restore it to unexecuted state")
    reset.set_defaults(func=reset_module)
    reset.add_argument("module_name", help="The name (or number) of the module to reset, or multiple separated by "
                                           "commas, or 'all' to reset the whole pipeline")
    reset.add_argument("-n", "--no-deps", action="store_true",
                       help="Only reset the state of this module, even if it has dependent modules in an executed "
                            "state, which could be invalidated by resetting and re-running this one")

    unlock = subparsers.add_parser("unlock",
                                   help="Forcibly remove an execution lock from a module. If a lock has ended up "
                                        "getting left on when execution exited prematurely, use this to remove it. "
                                        "Usually shouldn't be necessary, even if there's an error during execution")
    unlock.set_defaults(func=unlock_cmd)
    unlock.add_argument("module_name", help="The name (or number) of the module to unlock")

    longstore = subparsers.add_parser("longstore",
                                      help="Move a particular module's output from the short-term store to the long-term "
                                           "store. It will still be found here by input readers. You might want to do "
                                           "this if your long-term store is bigger, to keep down the short-term store size")
    longstore.set_defaults(func=short_to_long)
    longstore.add_argument("module_name", help="The name (or number) of the module whose output to move")

    browse = subparsers.add_parser("browse", help="View the data output by a module")
    browse.set_defaults(func=browse_cmd_with_deps)
    browse.add_argument("module_name", help="The name (or number) of the module whose output to look at. Use "
                                            "'module:stage' for multi-stage modules")
    browse.add_argument("output_name", nargs="?", help="The name of the output from the module to browse. If blank, "
                                                       "load the default output")
    browse.add_argument("--raw", "-r", action="store_true",
                        help="Don't parse the data using the output datatype (i.e. just read the raw text). If not "
                             "set, we output the result of applying unicode() to the parsed data structure, or a "
                             "custom formatting if the datatype loaded defines one")
    browse.add_argument("--formatter", "-f",
                        help="Fully qualified class name of a subclass of DocumentBrowserFormatter to use to determine "
                             "what to output for each document. If specified, --raw is ignored. You may also choose "
                             "from the named standard formatters for the datatype in question. Use '-f help' to see a "
                             "list of available formatters")

    shell = subparsers.add_parser("shell", help="Open a shell to give access to the data output by a module")
    shell.set_defaults(func=shell_cmd)
    shell.add_argument("module_name", help="The name (or number) of the module whose output to look at")
    shell.add_argument("output_name", nargs="?", help="The name of the output from the module to browse. If blank, "
                                                      "load the default output")

    install = subparsers.add_parser("install", help="Install missing module library dependencies")
    install.set_defaults(func=install_cmd)
    install.add_argument("modules", nargs="*",
                         help="Check dependencies for named modules and install any that are automatically "
                              "installable. Use 'all' to install dependencies for all modules")
    install.add_argument("--trust-downloaded", "-t", action="store_true",
                         help="If an archive file to be downloaded is found to be in the lib dir already, trust "
                              "that it is the file we're after. By default, we only reuse archives we've just "
                              "downloaded, so we know they came from the right URL, avoiding accidental name clashes")

    deps = subparsers.add_parser("deps", help="List information about software dependencies: whether they're "
                                              "available, versions, etc")
    deps.set_defaults(func=deps_cmd)
    deps.add_argument("modules", nargs="*",
                         help="Check dependencies for named modules and install any that are automatically "
                              "installable. Use 'all' to install dependencies for all modules")

    inputs = subparsers.add_parser("inputs",
                                   help="Show the locations of the inputs of a given module. If the input datasets "
                                        "are available, their actual location is shown. Otherwise, all directories "
                                        "in which the data is being checked for are shown")
    inputs.set_defaults(func=inputs_cmd)
    inputs.add_argument("module_name", help="The name (or number) of the module to display input locations for")

    output = subparsers.add_parser("output",
                                   help="Show the location where the given module's output data will be (or has been) "
                                        "stored")
    output.set_defaults(func=output_cmd)
    output.add_argument("module_name", help="The name (or number) of the module to display input locations for")

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

    # Set the process title (if possible) as "pimlico", plus the config filename
    # This might have no effect, if the system doesn't allow it
    set_proc_title("pimlico %s" % opts.pipeline_config)

    # Read in the pipeline config from the given file
    try:
        pipeline = PipelineConfig.load(opts.pipeline_config, variant=opts.variant,
                                       override_local_config=override_local)
    except PipelineConfigParseError, e:
        print >>sys.stderr, "Error reading pipeline config: %s" % e
        sys.exit(1)

    # Allow numbers to be used instead of module name arguments
    if hasattr(opts, "module_name") and opts.module_name is not None:
        opts.module_name = module_number_to_name(pipeline, opts.module_name)
    if hasattr(opts, "modules") and opts.modules is not None and len(opts.modules):
        opts.modules = [module_number_to_name(pipeline, name) for name in opts.modules]

    # Run the function corresponding to the subcommand
    opts.func(pipeline, opts)
