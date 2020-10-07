# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Tool for browsing datasets, reading from the data output by pipeline modules.
"""
from __future__ import print_function
import sys


def browse_cmd(pipeline, opts):
    """
    Command for main Pimlico CLI

    """
    module_name = opts.module_name
    output_name = opts.output_name
    print("Loading %s of module '%s'" % \
          ("default output" if output_name is None else "output '%s'" % output_name, module_name))
    reader_setup = pipeline[module_name].get_output_reader_setup(output_name)
    datatype = reader_setup.datatype
    print("Datatype: %s" % datatype.datatype_name)

    if not reader_setup.ready_to_read():
        print("Data not ready: cannot browse it", file=sys.stderr)
        sys.exit(1)

    # Get a reader for the corpus
    reader = reader_setup(pipeline, module_name)

    try:
        datatype.run_browser(reader, opts)
    except NotImplementedError as e:
        print("Datatype of this dataset ({}) does not provide a browser to view its data".format(
            datatype.datatype_name), file=sys.stderr)
        sys.exit(1)
