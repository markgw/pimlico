# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Main command-line script for running Pimlico, typically called from `pimlico.sh`.

Provides access to many subcommands, acting as the primary interface to Pimlico's functionality.

"""
if __name__ == "__main__":
    from pimlico import install_core_dependencies
    install_core_dependencies()

import argparse
import os
import sys
from operator import itemgetter

from pimlico.cli.check import check_cmd, install_cmd, deps_cmd
from pimlico.cli.loaddump import dump_cmd, load_cmd
from pimlico.cli.locations import inputs_cmd, output_cmd
from pimlico.cli.reset import reset_module
from pimlico.cli.run import run_cmd
from pimlico.cli.status import status_cmd
from pimlico.cli.util import module_number_to_name, module_numbers_to_names
from pimlico.core.config import PipelineConfig, PipelineConfigParseError
from pimlico.utils.filesystem import copy_dir_with_progress
from pimlico.utils.system import set_proc_title
from .shell.runner import shell_cmd


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
                                  help="[DEPRECATED: use status command to check pipeline, or run command with "
                                       "--dry-run to check modules instead.] "
                                       "Test a pipeline config to check that it can be parsed and is valid. It is "
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
    run.add_argument("--all-deps", "-a", action="store_true",
                     help="If the given module(s) has dependent modules that have not been completed, executed "
                          "them first. This allows you to specify a module late in the pipeline and execute the full "
                          "pipeline leading to that point")
    run.add_argument("--dry-run", "--dry", "--check", action="store_true",
                     help="Perform all pre-execution checks, but don't actually run the module(s)")

    variants = subparsers.add_parser("variants", help="List the available variants of a pipeline config")
    variants.set_defaults(func=list_variants)

    reset = subparsers.add_parser("reset",
                                  help="Delete any output from the given module and restore it to unexecuted state")
    reset.set_defaults(func=reset_module)
    reset.add_argument("modules", nargs="*",
                       help="The names (or numbers) of the modules to reset, or 'all' to reset the whole pipeline")
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

    dump = subparsers.add_parser("dump",
                                 help="Dump the entire available output data from a given pipeline module to a "
                                      "tarball, so that it can easily be loaded into the same pipeline on another "
                                      "system. This is primarily to support spreading the execution of a pipeline "
                                      "between multiple machines, so that the output from a module can easily be "
                                      "transferred and loaded into a pipeline")
    dump.set_defaults(func=dump_cmd)
    dump.add_argument("modules", nargs="*",
                      help="Names or numbers of modules whose data to dump. If multiple are given, a separate file "
                           "will be dumped for each")
    dump.add_argument("--output", "-o", help="Path to directory to output to. Defaults to the current user's home "
                                             "directory")

    load = subparsers.add_parser("load",
                                 help="Load a module's output data from a tarball previously created by the dump "
                                      "command, usually on a different system. This will overwrite any output data "
                                      "the module already has completely, including metadata, run history, etc. "
                                      "You may load multiple modules' data at once")
    load.set_defaults(func=load_cmd)
    load.add_argument("paths", nargs="*", help="Paths to dump files (tarballs) to load into the pipeline")

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
        opts.modules = module_numbers_to_names(pipeline, opts.modules)

    # Run the function corresponding to the subcommand
    opts.func(pipeline, opts)
