# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Main command-line script for running Pimlico, typically called from `pimlico.sh`.

Provides access to many subcommands, acting as the primary interface to Pimlico's functionality.

"""
from __future__ import print_function

from traceback import print_exc

from pimlico.cli.jupyter import JupyterCmd

if __name__ == "__main__":
    from pimlico import install_core_dependencies

    install_core_dependencies()

import argparse
import sys
from operator import itemgetter

from pimlico import cfg

from pimlico.cli.newmodule import NewModuleCmd
from pimlico.cli.check import InstallCmd, DepsCmd
from pimlico.cli.clean import CleanCmd
from pimlico.cli.loaddump import DumpCmd, LoadCmd
from pimlico.cli.locations import InputsCmd, OutputCmd, ListStoresCmd, MoveStoresCmd
from pimlico.cli.pyshell import PythonShellCmd
from pimlico.cli.reset import ResetCmd
from pimlico.cli.run import RunCmd
from pimlico.cli.shell.runner import ShellCLICmd
from pimlico.cli.status import StatusCmd
from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.cli.testemail import EmailCmd
from pimlico.cli.fixlength import FixLengthCmd
from pimlico.cli.recover import RecoverCmd
from pimlico.cli.util import module_number_to_name, module_numbers_to_names
from pimlico.core.config import PipelineConfig, PipelineConfigParseError, PipelineStructureError
from pimlico.core.modules.options import ModuleOptionParseError
from pimlico.utils.system import set_proc_title


class VariantsCmd(PimlicoCLISubcommand):
    """
    List the available variants of a pipeline config

    See :doc:`/core/variants` for more details.

    """
    command_name = "variants"
    command_help = "List the available variants of a pipeline config"

    def add_arguments(self, parser):
        pass

    def run_command(self, pipeline, opts):
        # Main is the default pipeline config and is always available (but not included in this list)
        variants = ["main"] + pipeline.available_variants
        print("Available pipeline variants: %s" % ", ".join(variants))
        print("Select one using the --variant option")


class UnlockCmd(PimlicoCLISubcommand):
    """
    Forcibly remove an execution lock from a module. If a lock has ended up
    getting left on when execution exited prematurely, use this to remove it.

    When a module starts running, it is locked to avoid making a mess of your output
    data by running the same module from another terminal, or some other silly mistake
    (I know, for some of us this sort of behaviour is frustratingly common).

    Usually shouldn't be necessary, even if there's an error during execution, since the
    module should be unlocked when Pimlico exits, but occasionally (e.g. if you have to
    forcibly kill Pimlico during execution) the lock gets left on.

    """
    command_name = "unlock"
    command_help = "Forcibly remove an execution lock from a module. If a lock has ended up " \
                   "getting left on when execution exited prematurely, use this to remove it. " \
                   "Usually shouldn't be necessary, even if there's an error during execution"
    command_desc = "Forcibly remove an execution lock from a module"

    def add_arguments(self, parser):
        parser.add_argument("module_name", help="The name (or number) of the module to unlock")

    def run_command(self, pipeline, opts):
        module = pipeline[opts.module_name]
        if not module.is_locked():
            print("Module '%s' is not locked" % opts.module_name)
        else:
            module.unlock()
            print("Module unlocked")


class BrowseCmd(PimlicoCLISubcommand):
    command_name = "browse"
    command_help = "View the data output by a module"

    def add_arguments(self, parser):
        parser.add_argument("module_name", help="The name (or number) of the module whose output to look at. Use "
                                                "'module:stage' for multi-stage modules")
        parser.add_argument("output_name", nargs="?", help="The name of the output from the module to browse. "
                                                           "If blank, load the default output")
        parser.add_argument("--skip-invalid", action="store_true",
                            help="Skip over invalid documents, instead of showing the error that caused them to be "
                                 "invalid")
        parser.add_argument("--formatter", "-f",
                            help="When browsing iterable corpora, fully qualified class name of a subclass of "
                                 "DocumentBrowserFormatter to use to determine what to output for each document. "
                                 "You may also choose from the named standard formatters for the datatype in question. "
                                 "Use '-f help' to see a list of available formatters")

    def run_command(self, pipeline, opts):
        # When this is first imported, it checks that it has its dependencies
        from .browser.tool import browse_cmd
        return browse_cmd(pipeline, opts)


class VisualizeCmd(PimlicoCLISubcommand):
    command_name = "visualize"
    command_help = "(Not yet fully implemented!) Visualize the pipeline, with status information for modules"
    command_desc = "Comming soon...visualize the pipeline in a pretty way"

    def add_arguments(self, parser):
        parser.add_argument("--all", "-a", action="store_true",
                            help="Show all modules defined in the pipeline, not just those that can be executed")

    def run_command(self, pipeline, opts):
        from pimlico.core.visualize.status import build_graph_with_status
        build_graph_with_status(pipeline, all=opts.all)


SUBCOMMANDS = [
    StatusCmd, VariantsCmd, RunCmd, RecoverCmd, FixLengthCmd, BrowseCmd, ShellCLICmd, PythonShellCmd, ResetCmd, CleanCmd,
    ListStoresCmd, MoveStoresCmd, UnlockCmd,
    DumpCmd, LoadCmd, DepsCmd, InstallCmd, InputsCmd, OutputCmd, NewModuleCmd, VisualizeCmd, EmailCmd,
    JupyterCmd,
]


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "setup":
        # Special case that doesn't require loading a pipeline
        # Don't complain about missing arguments, but just exit
        # If we've got this far, we've already been through the core dependency checks/installation, so they've
        #  already reported any problems or actions
        # This allows you to run Pimlico once after installation and perform basic setup without doing anything else
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Main command line interface to PiMLiCo")
    parser.add_argument("pipeline_config", help="Config file to load a pipeline from")
    parser.add_argument("--debug", "-d", help="Output verbose debugging info", action="store_true")
    parser.add_argument("--trace-config",
                        help="Trace the process of resolving which local config file(s) to use. Useful for debugging "
                             "the resolution on a given server or with a given set of config files",
                        action="store_true")
    parser.add_argument("--non-interactive",
                        help="Don't output things like progress bars that rely on being in a terminal or similar. "
                             "Equivalent to setting environment variable PIM_NON_INT=1",
                        action="store_true")
    parser.add_argument("--variant", "-v", help="Load a particular variant of a pipeline. For a list of available "
                                                "variants, use the 'variants' command", default="main")
    parser.add_argument("--override-local-config", "--local", "-l",
                        help="Override a parameter set in the local config files (usually ~/.pimlico). For just "
                             "this execution. Specify as param=value. Use this option multiple times to override "
                             "more than one parameter", action="append")
    parser.add_argument("--local-config", "--lc",
                        help="Load local config from a given config file, instead of from the default location, "
                             "~/.pimlico. Command-line overrides (see --override-local-config) will still be "
                             "applied, but the standard config file will not be loaded, nor any hostname-specific "
                             "config files")
    parser.add_argument("--processes", "-p",
                        help="Set the number of processes to use for this run, where parallelization is available. "
                             "Overrides the local config setting. Equivalent to '-l processes=P'", type=int)
    subparsers = parser.add_subparsers(help="Select a sub-command")

    # Add all subcommands that have been defined using the class interface
    for subcommand_cls in SUBCOMMANDS:
        # Instantiate the class
        subcommand = subcommand_cls()
        # Use it to add a subcommand to the arg parser
        subparser = subparsers.add_parser(subcommand.command_name, help=subcommand.command_help)
        subparser.set_defaults(func=subcommand.run_command)
        # Add subparser arguments as defined by the individual subcommand class
        subcommand.add_arguments(subparser)

    opts = parser.parse_args()

    if opts.override_local_config is not None:
        override_local = dict(
            itemgetter(0, 2)(param.partition("=")) for param in opts.override_local_config
        )
    else:
        override_local = {}

    if opts.trace_config:
        # Trace the loading of local config files
        if opts.override_local_config is not None:
            print("Using some local config overrides from command line: {}".format(
                ", ".join(opts.override_local_config)))
        if opts.local_config:
            print("Using local config source given on command line: {}".format(opts.local_config))

        # Run the usual LC loading routine that the pipeline config loader uses
        for l, line in enumerate(
                PipelineConfig.trace_load_local_config(filename=opts.local_config, override=override_local)):
            print("{}: {}".format(l, line))
        sys.exit(0)

    if opts.processes is not None:
        # Override the processes local config setting
        override_local["processes"] = opts.processes

    # Set the process title (if possible) as "pimlico", plus the config filename
    # This might have no effect, if the system doesn't allow it
    set_proc_title("pimlico %s" % opts.pipeline_config)

    if opts.non_interactive:
        cfg.NON_INTERACTIVE_MODE = True

    # Read in the pipeline config from the given file
    try:
        pipeline = PipelineConfig.load(opts.pipeline_config, variant=opts.variant,
                                       override_local_config=override_local,
                                       local_config=opts.local_config)
    except (PipelineConfigParseError, PipelineStructureError) as e:
        if opts.debug:
            print_exc()
        print("Error reading pipeline config: %s" % e, file=sys.stderr)
        if hasattr(e, "explanation") and e.explanation is not None:
            # Show more detailed explanation of problem
            print("\n" + e.explanation, file=sys.stderr)
        sys.exit(1)
    except ModuleOptionParseError as e:
        print("Error in module options specified in config file: %s" % e, file=sys.stderr)
        sys.exit(1)

    # Allow numbers to be used instead of module name arguments
    try:
        if hasattr(opts, "module_name") and opts.module_name is not None:
            opts.module_name = module_number_to_name(pipeline, opts.module_name)
        if hasattr(opts, "modules") and opts.modules is not None and len(opts.modules):
            opts.modules = module_numbers_to_names(pipeline, opts.modules)
        if hasattr(opts, "module") and opts.module is not None:
            opts.module = module_number_to_name(pipeline, opts.module)
    except ValueError as e:
        print("Error in module specification: %s" % e, file=sys.stderr)
        sys.exit(1)

    # Run the function corresponding to the subcommand
    opts.func(pipeline, opts)
