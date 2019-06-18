# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
import copy

from pimlico.cli.recover import count_docs
from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.core.modules.base import satisfies_typecheck
from pimlico.datatypes import GroupedCorpus, PimlicoDatatype
from pimlico.datatypes.base import DataNotReadyError, _metadata_path
from pimlico.datatypes.corpora.data_points import RawDocumentType


class FixLengthCmd(PimlicoCLISubcommand):
    """
    Under some circumstances (e.g. some unpredictable combinations of failures
    and restarts), an output corpus can end up with an incorrect length in its
    metadata. This command counts up the documents in the corpus and corrects
    the stored length if it's wrong.

    """
    command_name = "fixlength"
    command_help = "Check the length of written outputs and fix it if it's wrong"

    def add_arguments(self, parser):
        parser.add_argument("module", help="The name (or number) of the module to recover")
        parser.add_argument("outputs", nargs="*", help="Names of module outputs to check. By default, checks all")
        parser.add_argument("--dry", action="store_true", help="Dry run: check the lengths, but don't write anything")

    def run_command(self, pipeline, opts):
        dry = opts.dry
        module_name = opts.module
        module = pipeline[module_name]

        # Get the outputs that are grouped corpora
        grouped_outputs = [
            name for name in module.output_names
            if satisfies_typecheck(module.get_output_datatype(name)[1], GroupedCorpus(RawDocumentType()))
        ]
        if opts.outputs:
            # Some specific module names have been given
            for output_name in opts.outpus:
                if output_name not in module.output_names:
                    raise ValueError("unknown output '{}' for module '{}'".format(output_name, module_name))
                if output_name not in grouped_outputs:
                    raise ValueError("output '{}' is not a grouped corpus".format(output_name))
            outputs = opts.outputs
        else:
            # Check all grouped corpus outputs
            outputs = grouped_outputs

        print "Checking outputs: {}".format(", ".join(outputs))
        for output_name in outputs:
            print "\n### Checking output '{}'".format(output_name)
            try:
                output = module.get_output(output_name)
            except DataNotReadyError, e:
                print "Could not read output '{}': cannot check written documents".format(output_name)
                raise DataNotReadyError("could not read output '{}': {}".format(output_name, e))
            print "Reported length: {:,d}".format(len(output))
            print "Counting actual length. This could take some time..."
            # Use the function from the recover command to count the docs
            num_docs = count_docs(output, last_buffer_size=0)[1]
            if num_docs == len(output):
                print "Reported length is correct"
            else:
                print "Stored length does not match number of docs"
                print "Actual length: {:,d}".format(num_docs)
                if dry:
                   print "DRY: Not correcting metadata"
                else:
                    metadata_path = _metadata_path(output.base_dir)
                    print "Correcting metadata in {}".format(metadata_path)
                    metadata = copy.deepcopy(output.metadata)
                    metadata["length"] = num_docs
                    # Use standard method to write out the corrected metadata
                    PimlicoDatatype.Writer._write_metadata(metadata_path, metadata)
