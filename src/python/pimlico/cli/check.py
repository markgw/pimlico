from __future__ import print_function

from pimlico.core.dependencies.core import CORE_PIMLICO_DEPENDENCIES

from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.core.config import get_dependencies
from pimlico.core.dependencies.base import install_dependencies
from pimlico.core.dependencies.licenses import NOT_RELEVANT
from pimlico.utils.format import title_box


# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html


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


class LicensesCmd(PimlicoCLISubcommand):
    """
    Output a list of the licenses for all software depended on.

    """
    command_name = "licenses"
    command_help = "List information about licsenses of software dependencies"

    def add_arguments(self, parser):
        parser.add_argument("modules", nargs="*",
                            help="Check dependencies of modules and their datatypes. "
                                 "Use 'all' to list licenses for dependencies for all modules")

    def run_command(self, pipeline, opts):
        if "all" in opts.modules or len(opts.modules) == 0:
            # Install for all modules
            modules = None
        else:
            modules = opts.modules

        deps = get_dependencies(pipeline, modules, recursive=True)
        # Always include the core dependencies
        deps.extend(CORE_PIMLICO_DEPENDENCIES)

        print("The list below covers the licenses of all software that \n"
              "is used to run this pipeline, grouped by license.\n"
              "If a license is unknown, you should check the software's \n"
              "homepage or source code for a license.\n")

        # Group by license
        licenses = {}
        for dep in deps:
            if dep.license is not NOT_RELEVANT:
                licenses.setdefault(dep.license, []).append(dep)

        for license, lic_deps in licenses.items():
            if license is None:
                print(title_box("License unknown"))
                print("Check the software's homepage for a license\n")
            else:
                print(title_box(license.name))

            for dep in lic_deps:
                # If there's no license, show a link to the homepage if possible
                if license is None and dep.homepage_url is not None:
                    homepage = " ({})".format(dep.homepage_url)
                else:
                    homepage = ""
                print("{}{}".format(dep.name, homepage))
            print()
