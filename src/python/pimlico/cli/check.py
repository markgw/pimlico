from __future__ import print_function
# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.core.config import get_dependencies
from pimlico.core.dependencies.base import install_dependencies
from pimlico.utils.format import title_box


class InstallCmd(PimlicoCLISubcommand):
    """
    Install missing dependencies.

    """
    command_name = "install"
    command_help = "Install missing module library dependencies"

    def add_arguments(self, parser):
        parser.add_argument("modules", nargs="*",
                            help="Check dependencies for named modules and install any that are automatically "
                                 "installable. Use 'all' to install dependencies for all modules")
        parser.add_argument("--trust-downloaded", "-t", action="store_true",
                            help="If an archive file to be downloaded is found to be in the lib dir already, trust "
                                 "that it is the file we're after. By default, we only reuse archives we've just "
                                 "downloaded, so we know they came from the right URL, avoiding accidental name clashes")

    def run_command(self, pipeline, opts):
        if "all" in opts.modules:
            # Install for all modules
            modules = None
        else:
            modules = opts.modules
        install_dependencies(pipeline, modules, trust_downloaded_archives=opts.trust_downloaded)


class DepsCmd(PimlicoCLISubcommand):
    """
    Output information about module dependencies.

    """
    command_name = "deps"
    command_help = "List information about software dependencies: whether they're available, versions, etc"

    def add_arguments(self, parser):
        parser.add_argument("modules", nargs="*",
                            help="Check dependencies for named modules and install any that are automatically "
                                 "installable. Use 'all' to install dependencies for all modules")

    def run_command(self, pipeline, opts):
        if "all" in opts.modules or len(opts.modules) == 0:
            # Install for all modules
            modules = None
        else:
            modules = opts.modules
        deps = get_dependencies(pipeline, modules, recursive=True)

        for dep in deps:
            print()
            print(title_box(dep.name.capitalize()))
            if dep.available(pipeline.local_config):
                print("Installed")
                print("Version: %s" % dep.get_installed_version(pipeline.local_config))
            elif dep.installable():
                print("Can be automatically installed with the 'install' command")
            else:
                print("Cannot be automatically installed")
                print(dep.installation_instructions())
