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

from pimlico.cli.newmodule import NewModuleCmd
from pimlico.cli.check import InstallCmd, DepsCmd
from pimlico.cli.clean import CleanCmd
from pimlico.cli.loaddump import DumpCmd, LoadCmd
from pimlico.cli.locations import InputsCmd, OutputCmd
from pimlico.cli.pyshell import PythonShellCmd
from pimlico.cli.reset import ResetCmd
from pimlico.cli.run import RunCmd
from pimlico.cli.shell.runner import ShellCLICmd
from pimlico.cli.status import StatusCmd
from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.cli.testemail import EmailCmd
from pimlico.cli.util import module_number_to_name, module_numbers_to_names
from pimlico.core.config import PipelineConfig, PipelineConfigParseError, PipelineStructureError
from pimlico.core.modules.options import ModuleOptionParseError
from pimlico.utils.filesystem import copy_dir_with_progress
from pimlico.utils.system import set_proc_title


class VariantsCmd(PimlicoCLISubcommand):
    command_name = "variants"
    command_help = "List the available variants of a pipeline config"

    def add_arguments(self, parser):
        pass

    def run_command(self, pipeline, opts):
        # Main is the default pipeline config and is always available (but not included in this list)
        variants = ["main"] + pipeline.available_variants
        print "Available pipeline variants: %s" % ", ".join(variants)
        print "Select one using the --variant option"


class LongStoreCmd(PimlicoCLISubcommand):
    command_name = "longstore"
    command_help = "Move a particular module's output from the short-term store to the long-term " \
                   "store. It will still be found here by input readers. You might want to do " \
                   "this if your long-term store is bigger, to keep down the short-term store size"
    command_desc = "Move a particular module's output from the short-term store to the long-term store"

    def add_arguments(self, parser):
        parser.add_argument("modules", nargs="*", help="The names (or numbers) of the module whose output to move")

    def run_command(self, pipeline, opts):
        print "Copying modules from short-term to long-term store: %s" % ", ".join(opts.modules)
        for module_name in opts.modules:
            # Get the path within the stores
            module_path = pipeline[module_name].get_module_output_dir()
            # Work out where it lives in the short-term and long-term stores
            short_term_dir = os.path.join(pipeline.short_term_store, module_path)
            long_term_dir = os.path.join(pipeline.long_term_store, module_path)
            if not os.path.exists(short_term_dir):
                print "Output dir %s does not exist, cannot move" % short_term_dir
            elif short_term_dir == long_term_dir:
                print "Short-term dir is the same as long-term dir (%s), not moving" % short_term_dir
            else:
                copy_dir_with_progress(short_term_dir, long_term_dir)


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
            print "Module '%s' is not locked" % opts.module_name
        else:
            module.unlock()
            print "Module unlocked"


class BrowseCmd(PimlicoCLISubcommand):
    command_name = "browse"
    command_help = "View the data output by a module"

    def add_arguments(self, parser):
        parser.add_argument("module_name", help="The name (or number) of the module whose output to look at. Use "
                                                "'module:stage' for multi-stage modules")
        parser.add_argument("output_name", nargs="?", help="The name of the output from the module to browse. If blank, "
                                                           "load the default output")
        parser.add_argument("--raw", "-r", action="store_true",
                            help="Don't parse the data using the output datatype (i.e. just read the raw text). If not "
                                 "set, we output the result of applying unicode() to the parsed data structure, or a "
                                 "custom formatting if the datatype loaded defines one")
        parser.add_argument("--skip-invalid", action="store_true",
                            help="Skip over invalid documents, instead of showing the error that caused them to be "
                                 "invalid")
        parser.add_argument("--formatter", "-f",
                            help="Fully qualified class name of a subclass of DocumentBrowserFormatter to use to determine "
                                 "what to output for each document. If specified, --raw is ignored. You may also choose "
                                 "from the named standard formatters for the datatype in question. Use '-f help' to see a "
                                 "list of available formatters")

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
    StatusCmd, VariantsCmd, RunCmd, BrowseCmd, ShellCLICmd, PythonShellCmd, ResetCmd, CleanCmd, LongStoreCmd, UnlockCmd,
    DumpCmd, LoadCmd, DepsCmd, InstallCmd, InputsCmd, OutputCmd, NewModuleCmd, VisualizeCmd, EmailCmd
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Main command line interface to PiMLiCo")
    parser.add_argument("pipeline_config", help="Config file to load a pipeline from")
    parser.add_argument("--debug", "-d", help="Output verbose debugging info", action="store_true")
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
    if opts.processes is not None:
        # Override the processes local config setting
        override_local["processes"] = opts.processes

    # Set the process title (if possible) as "pimlico", plus the config filename
    # This might have no effect, if the system doesn't allow it
    set_proc_title("pimlico %s" % opts.pipeline_config)

    # Read in the pipeline config from the given file
    try:
        pipeline = PipelineConfig.load(opts.pipeline_config, variant=opts.variant,
                                       override_local_config=override_local,
                                       local_config=opts.local_config)
    except (PipelineConfigParseError, PipelineStructureError), e:
        print >>sys.stderr, "Error reading pipeline config: %s" % e
        sys.exit(1)
    except ModuleOptionParseError, e:
        print >>sys.stderr, "Error in module options specified in config file: %s" % e
        sys.exit(1)

    # Allow numbers to be used instead of module name arguments
    try:
        if hasattr(opts, "module_name") and opts.module_name is not None:
            opts.module_name = module_number_to_name(pipeline, opts.module_name)
        if hasattr(opts, "modules") and opts.modules is not None and len(opts.modules):
            opts.modules = module_numbers_to_names(pipeline, opts.modules)
    except ValueError, e:
        print >>sys.stderr, "Error in module specification: %s" % e
        sys.exit(1)

    # Run the function corresponding to the subcommand
    opts.func(pipeline, opts)
