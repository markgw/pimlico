# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
from __future__ import print_function
from builtins import input

from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.utils.core import remove_duplicates


class ResetCmd(PimlicoCLISubcommand):
    command_name = "reset"
    command_help = "Delete any output from the given module and restore it to unexecuted state"

    def add_arguments(self, parser):
        parser.add_argument("modules", nargs="*",
                            help="The names (or numbers) of the modules to reset, or 'all' to reset the whole pipeline")
        parser.add_argument("-n", "--no-deps", action="store_true",
                            help="Only reset the state of this module, even if it has dependent modules in an executed "
                                 "state, which could be invalidated by resetting and re-running this one")
        parser.add_argument("-f", "--force-deps", action="store_true",
                            help="Reset the state of this module and any dependent modules in an executed "
                                 "state, which could be invalidated by resetting and re-running this one. Do "
                                 "not ask for confirmation to do this")

    def run_command(self, pipeline, opts):
        if "all" in opts.modules:
            # Reset every module, one by one
            print("Resetting execution state of all modules")
            pipeline.reset_all_modules()
        else:
            module_names = opts.modules
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
                    print("The following modules depend on %s. Their execution state will be reset too if you continue." % \
                          ", ".join(module_names))
                    print("  %s" % ", ".join(dependent_modules))
                    if opts.force_deps:
                        print("Resetting all")
                    else:
                        answer = input("Do you want to continue? [y/N] ")
                        if answer.lower() != "y":
                            print("Cancelled")
                            return

            for module_name in module_names + dependent_modules:
                print("Resetting execution state of module %s" % module_name)
                module = pipeline[module_name]
                module.reset_execution()
