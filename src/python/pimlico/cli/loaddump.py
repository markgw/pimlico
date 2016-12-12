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


def dump_cmd(pipeline, opts):
    """
    Command to dump the output data from a given pipeline module to a tarball.

    """
    output_dir = opts.output
    if output_dir is None:
        # Default to current user's home dir
        output_dir = os.path.expanduser("~")
    output_dir = os.path.abspath(output_dir)

    for module_name in opts.modules:
        print "== Dumping data for '%s' ==" % module_name
        module = pipeline[module_name]
        # Get the output dir for the module
        module_output_dir = module.get_module_output_dir(short_term_store=True)
        # Work out where to put the output
        tarball_path = os.path.join(output_dir, "%s.tar.gz" % module_name)
        print "Dumping to %s" % tarball_path

        with tarfile.open(tarball_path, mode="w:gz") as tarball:
            # Prepare a file containing a bit of metadata that will be read by Pimlico if the data is loaded
            dump_meta = json.dumps({
                "pipeline_name": pipeline.name,
                "module_name": module_name,
                # Just so we know where this came from...
                "dumped": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hostname": socket.gethostname(),
            }, indent=4)
            meta_info = tarfile.TarInfo("dump_metadata.json")
            meta_info.size = len(dump_meta)
            tarball.addfile(meta_info, StringIO(dump_meta))

            # Add the module's output directory to the tarball (recursively)
            tarball.add(module_output_dir, arcname=module_name)


def load_cmd(pipeline, opts):
    """
    Command to load the output data for a given pipeline module from a tarball previously created by the
    `dump` command (typically on another machine).

    """
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

            module = pipeline[module_name]
            # Get the output dir for the module
            module_output_dir = module.get_module_output_dir(short_term_store=True)
            print "Extracting module data to %s" % module_output_dir
            # If the output dir already exists, delete it first
            if os.path.exists(module_output_dir):
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
