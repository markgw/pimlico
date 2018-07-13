# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
import json
import os
import shutil
import socket
import tarfile

import sys
from datetime import datetime
from cStringIO import StringIO

from pimlico.cli.subcommands import PimlicoCLISubcommand


class DumpCmd(PimlicoCLISubcommand):
    """
    Dump the entire available output data from a given pipeline module to a
    tarball, so that it can easily be loaded into the same pipeline on another
    system. This is primarily to support spreading the execution of a pipeline
    between multiple machines, so that the output from a module can easily be
    transferred and loaded into a pipeline.

    Dump to a tarball using this command, transfer the file between machines and
    then run the :doc:`load command </commands/load>` to import it there.

    .. seealso::

       :doc:`/guides/multiple_servers`: for a more detailed guide to transferring data across servers

    """
    command_name = "dump"
    command_help = "Dump the entire available output data from a given pipeline module to a " \
                   "tarball, so that it can easily be loaded into the same pipeline on another " \
                   "system. This is primarily to support spreading the execution of a pipeline " \
                   "between multiple machines, so that the output from a module can easily be " \
                   "transferred and loaded into a pipeline"
    command_desc = "Dump the entire available output data from a given pipeline module to a tarball"

    def add_arguments(self, parser):
        parser.add_argument("modules", nargs="*",
                            help="Names or numbers of modules whose data to dump. If multiple are given, a separate "
                                 "file will be dumped for each")
        parser.add_argument("--output", "-o",
                            help="Path to directory to output to. Defaults to the current user's home directory")

    def run_command(self, pipeline, opts):
        output_dir = opts.output
        if output_dir is None:
            # Default to current user's home dir
            output_dir = os.path.expanduser("~")
        output_dir = os.path.abspath(output_dir)

        for module_name in opts.modules:
            print "== Dumping data for '%s' ==" % module_name
            try:
                module = pipeline[module_name]
            except KeyError:
                print >>sys.stderr, "Error: module '{}' does not exist".format(module_name)
                continue

            # Get the output dir for the module
            module_rel_output_dir = module.get_module_output_dir()
            # See if it exists in any store
            store_name, module_abs_output_dir = pipeline.find_data(module_rel_output_dir)
            if store_name is None:
                print "Could not find any output data for module '{}'. Not dumping anything".format(module_name)
                continue
            else:
                print "Data found in {} store".format(store_name)

            # Work out where to put the output
            tarball_path = os.path.join(output_dir, "%s.tar.gz" % module_name)
            print "Dumping to %s\n" % tarball_path

            with tarfile.open(tarball_path, mode="w:gz") as tarball:
                # Prepare a file containing a bit of metadata that will be read by Pimlico if the data is loaded
                dump_meta = json.dumps({
                    "pipeline_name": pipeline.name,
                    "module_name": module_name,
                    # Just so we know where this came from...
                    "dumped": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "hostname": socket.gethostname(),
                    "variant": pipeline.variant,
                }, indent=4)
                meta_info = tarfile.TarInfo("dump_metadata.json")
                meta_info.size = len(dump_meta)
                tarball.addfile(meta_info, StringIO(dump_meta))

                # Add the module's output directory to the tarball (recursively)
                tarball.add(module_abs_output_dir, arcname=module_name)


class LoadCmd(PimlicoCLISubcommand):
    """
    Load the output data for a given pipeline module from a tarball previously created by the
    `dump` command (typically on another machine).
    This is primarily to support spreading the execution of a pipeline
    between multiple machines, so that the output from a module can easily be
    transferred and loaded into a pipeline.

    Dump to a tarball using the :doc:`dump command </commands/dump>`,
    transfer the file between machines and
    then run this command to import it there.

    .. seealso::

       :doc:`/guides/multiple_servers`: for a more detailed guide to transferring data across servers

    """
    command_name = "load"
    command_help = "Load a module's output data from a tarball previously created by the dump " \
                   "command, usually on a different system. This will overwrite any output data " \
                   "the module already has completely, including metadata, run history, etc. " \
                   "You may load multiple modules' data at once"
    command_desc = "Load a module's output data from a tarball previously created by the dump command"

    def add_arguments(self, parser):
        parser.add_argument("paths", nargs="*", help="Paths to dump files (tarballs) to load into the pipeline")
        parser.add_argument("--force-overwrite", "-f", action="store_true",
                            help="If data already exists for a module being imported, overwrite without asking. "
                                 "By default, the user will be prompted to check whether they want to overwrite")

    def run_command(self, pipeline, opts):
        force_overwrite = opts.force_overwrite

        for dump_path in opts.paths:
            dump_path = os.path.abspath(dump_path)

            # Try reading a tarball at the given path
            with tarfile.open(dump_path, mode="r:gz") as tarball:
                # Tarball should include a metadata file if it's come from a dump
                metadata_file = tarball.extractfile("dump_metadata.json")
                dump_meta = json.loads(metadata_file.read())
                metadata_file.close()

                module_name = dump_meta["module_name"]
                print "== Loading data for '%s' from %s ==" % (module_name, dump_path)

                # Check that the pipeline that this was dumped from had the same name
                # This is just a weak sanity check to avoid mixing up data between pipelines
                # In future, it may be desirable to add a '-f' switch to override this check
                if pipeline.name != dump_meta["pipeline_name"]:
                    print >>sys.stderr, "Error: the dumped data came from a pipeline called '%s', but you're trying to " \
                                        "load it into '%s'" % (dump_meta["pipeline_name"], pipeline.name)
                    sys.exit(1)
                # Also check we've loaded the correct variant of the pipeline
                # Would be nice to just load the right one automatically, but it's tricky to go back and load it again
                # Instead, just output an error, so the user can load the right one
                dump_variant = dump_meta.get("variant", "main")
                if pipeline.variant != dump_variant:
                    print >>sys.stderr, "Error: the dumped data came from the '%s' variant of the pipeline, " \
                                        "but you're trying to load it into '%s'. Load the correct variant with '-v'" % \
                                        (dump_variant, pipeline.variant)
                    sys.exit(1)

                try:
                    module = pipeline[module_name]
                except KeyError:
                    print >>sys.stderr, \
                        "Error: module with name '{}' does not exist in the pipeline".format(module_name)
                    continue

                # Get the output dir for the module
                module_output_dir = module.get_module_output_dir(absolute=True)
                print "Extracting module data to %s" % module_output_dir
                # If the output dir already exists, delete it first
                if os.path.exists(module_output_dir):
                    if not force_overwrite:
                        # In this case, check we're happy to overwrite
                        sure = raw_input("Module output dir already exists. Overwrite? [y/N] ")
                        if sure.lower() != "y":
                            print "Skipping %s" % module_name
                            continue

                    shutil.rmtree(module_output_dir)

                # Extract the directory into the module output dir's super directory (i.e. the pipeline dir)
                extraction_dir = os.path.dirname(module_output_dir)
                to_extract = [tarinfo for tarinfo in tarball.getmembers() if tarinfo.name.startswith("%s/" % module_name)]
                tarball.extractall(path=extraction_dir, members=to_extract)
                print "Data loaded"
