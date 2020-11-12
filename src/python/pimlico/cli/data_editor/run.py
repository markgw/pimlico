import sys
import argparse
from code import interact

import os

from pimlico.datatypes import load_datatype

from pimlico.core.config import PipelineConfig


def run_editor(dataset_root, datatype_name):
    # Create an empty pipeline
    pipeline = PipelineConfig.empty()
    local = {"pipeline": pipeline, "p": pipeline}
    print("Empty PipelineConfig object is available as variable 'pipeline' (or 'p')")
    # Trying loading the datatype
    datatype = load_datatype(datatype_name)
    print("Loaded datatype: {}".format(datatype))

    if not os.path.exists(dataset_root):
        # *** Write mode ***
        print("Creating a new dataset at {}".format(dataset_root))
        # Create a writer
        # TODO We should allow different args/kwargs to be passed in here
        writer = datatype.get_writer(dataset_root, pipeline)
        print("Created dataset writer".format(dataset_root))
        print("Writer is available as variable 'writer' (or 'w')")
        local["writer"] = local["w"] = writer
    else:
        # *** Read mode ***
        print("Attempting to read a dataset of type {} from {}".format(datatype, dataset_root))
        # Create a reader, via a reader setup
        setup = datatype([dataset_root])
        if not setup.ready_to_read():
            print("Data not ready to read from {}".format(dataset_root))
            print("Reader setup available as variable 'setup'")
            local["setup"] = setup
        else:
            reader = setup(pipeline)
            print("Dataset loaded. Reader available as variable 'reader' (or 'r')")
            local["reader"] = local["r"] = reader

    # Enter the interpreter
    interact(local=local)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dataset editor tool")
    parser.description = """\
Either edits an existing dataset (not yet implemented) or creates a new one.

If the given path exists, we attempt to load a dataset of the given 
datatype from there and an appropriate reader is created.

Otherwise, an appropriate writer will be created, writing data to the 
given dataset root.

You are then taken to a Python shell, where you can access to reader or 
writer to manipulate the dataset.

"""
    parser.add_argument("dataset_root", help="Root directory for the dataset")
    parser.add_argument("datatype", help="PimlicoDatatype to use to create a new dataset or read the existing one. "
                                         "Given as a fully qualified path, or a shortcut. "
                                         "See pimlico.datatypes.load_datatype() for more details")
    opts = parser.parse_args()

    run_editor(opts.dataset_root, opts.datatype)
