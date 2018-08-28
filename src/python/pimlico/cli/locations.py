# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
import os
import sys

from tabulate import tabulate

from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.utils.core import remove_duplicates
from pimlico.utils.filesystem import move_dir_with_progress


class InputsCmd(PimlicoCLISubcommand):
    command_name = "inputs"
    command_help = "Show the locations of the inputs of a given module. If the input datasets " \
                   "are available, their actual location is shown. Otherwise, all directories " \
                   "in which the data is being checked for are shown"
    command_desc = "Show the (expected) locations of the inputs of a given module"

    def add_arguments(self, parser):
        parser.add_argument("module_name", help="The name (or number) of the module to display input locations for")

    def run_command(self, pipeline, opts):
        module_name = opts.module_name
        print "Input locations for module '%s'" % module_name
        try:
            module = pipeline[module_name]
        except KeyError:
            print >>sys.stderr, "Error: module '{}' does not exist".format(module_name)
            sys.exit(1)

        # Display info for each input to this module
        for input_name in module.input_names:
            print "\nInput '%s'" % input_name
            input_setup_lst = module.get_input_reader_setup(input_name, always_list=True)
            input_connections = module.get_input_module_connection(input_name, always_list=True)
            multiple_inputs = len(input_setup_lst) > 1
            if multiple_inputs:
                print "Multiple input sources: showing locations for all"

            for i, (input_setup, (prev_module, prev_output_name)) in enumerate(zip(input_setup_lst, input_connections)):
                if multiple_inputs:
                    print "## Input source %d ##" % i

                input_datatype = input_setup.datatype
                if input_setup.ready_to_read():
                    # Get the input reader
                    input_reader = input_setup(pipeline, module_name)
                    if hasattr(input_reader, "base_dir") and input_reader.base_dir is not None:
                        print "Data (%s) available in:" % input_datatype.full_datatype_name()
                        print " - %s" % input_reader.base_dir
                    else:
                        print "Data (%s) available, but no directory given: perhaps a filter datatype" % \
                              input_datatype.full_datatype_name()
                else:
                    if hasattr(input_setup, "data_paths") and len(input_setup.data_paths) > 0:
                        print "Data not available. Data will be found in any of the following locations:"
                        # Get the relative dir within the Pimlico dir structures
                        rel_path = prev_module.get_output_dir(prev_output_name)
                        # Resolve this to all possible absolute dirs (usually two)
                        abs_paths = remove_duplicates([path for (name, path) in pipeline.get_data_search_paths(rel_path)])
                        print "\n".join(" - %s" % pth for pth in abs_paths)
                    else:
                        print "Data not available. No possible data locations available, perhaps a filter datatype"


class OutputCmd(PimlicoCLISubcommand):
    command_name = "output"
    command_help = "Show the location where the given module's output data will be (or has been) stored"

    def add_arguments(self, parser):
        parser.add_argument("module_name", help="The name (or number) of the module to display input locations for")

    def run_command(self, pipeline, opts):
        module_name = opts.module_name
        try:
            module = pipeline[module_name]
        except KeyError:
            print >>sys.stderr, "Error: module '{}' does not exist".format(module_name)
            sys.exit(1)
        # Get the output dir for the module
        module_output_dir = module.get_module_output_dir(absolute=True)
        print "Output location for module '%s': %s" % (module_name, module_output_dir)


class ListStoresCmd(PimlicoCLISubcommand):
    command_name = "stores"
    command_help = "List Pimlico stores in use and the corresponding storage locations"
    command_desc = "List named Pimlico stores"

    def run_command(self, pipeline, opts):
        print "Absolute paths to named storage locations\n"
        print tabulate(pipeline.storage_locations, ["Name", "Path"])


class MoveStoresCmd(PimlicoCLISubcommand):
    command_name = "movestores"
    command_help = "Move a particular module's output from one storage location to another"
    command_desc = "Move data between stores"

    def add_arguments(self, parser):
        parser.add_argument("dest", help="Name of destination store")
        parser.add_argument("modules", nargs="*", help="The names (or numbers) of the module whose output to move")

    def run_command(self, pipeline, opts):
        raise NotImplementedError("not yet updated for the new datatypes system: not safe to use!")
        dest_store = opts.dest
        if dest_store not in pipeline.store_names:
            print >>sys.stderr, "No such store: {}".format(dest_store)
            print >>sys.stderr, "Available store names: {}".format(", ".join(pipeline.store_names))

        print "Copying modules to store '%s': %s" % (opts.dest, ", ".join(opts.modules))
        for module_name in opts.modules:
            # Get the path within the stores
            module_path = pipeline[module_name].get_module_output_dir()
            # Check which store the module's data is currently in
            # TODO Update this for the new datatype system
            src_store, src_path = pipeline.find_data(module_path)
            if src_store is None:
                print >>sys.stderr, "Cannot move data for '{}' as it wasn't found in any store".format(module_name)
                continue
            elif src_store == dest_store:
                print >>sys.stderr, "Skipping '{}' as it's alreay in store '{}'".format(module_name, dest_store)
                continue

            print "Copying '{}' data from {} to {}".format(module_name, src_store, dest_store)
            # Work out where it will lives in the dest store
            dest_path = os.path.join(pipeline.named_storage_locations[dest_store], module_path)
            move_dir_with_progress(src_path, dest_path)
