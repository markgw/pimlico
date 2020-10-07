# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import print_function

import os
from tarfile import TarFile

from pimlico.cli.subcommands import PimlicoCLISubcommand
from pimlico.core.modules.base import satisfies_typecheck
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.base import DataNotReadyError
from pimlico.utils.pimarc import PimarcWriter


class Tar2PimarcCmd(PimlicoCLISubcommand):
    """
    Convert grouped corpora from the old tar-based storage format to Pimarc
    archives.

    """
    command_name = "tar2pimarc"
    command_help = "Convert grouped corpora from the old tar-based storage format to pimarc"

    def add_arguments(self, parser):
        parser.add_argument("outputs", nargs="*",
                            help="Specification of module outputs to convert. Specific datasets can "
                                 "be given as 'module_name.output_name'. All grouped corpus outputs "
                                 "of a module can be converted by just giving 'module_name'. Or, if "
                                 "nothing's given, all outputs of all modules are converted")
        parser.add_argument("--run", action="store_true",
                            help="Run conversion. Without this option, just checks "
                                 "what format the corpora use")

    def run_command(self, pipeline, opts):
        run = opts.run
        if not run:
            print("DRY: Not running any conversions, just checking formats")

        output_specs = opts.outputs
        if output_specs is None or len(output_specs) == 0:
            # Nothing given: convert all modules
            outputs = []
            for module_name in pipeline.module_order:
                # Check module for any grouped corpus outputs
                module = pipeline[module_name]
                grouped_outputs = [
                    name for name in module.output_names
                    if satisfies_typecheck(module.get_output_datatype(name)[1], GroupedCorpus())
                ]
                module_outputs = [(module_name, output) for output in grouped_outputs]
                if len(module_outputs):
                    print("Including: {}".format(", ".join("{}.{}".format(mn, on) for (mn, on) in module_outputs)))
                    outputs.extend(module_outputs)
                else:
                    print("No grouped corpus outputs from {}".format(module_name))
        else:
            outputs = []
            for output_spec in output_specs:
                if "." in output_spec:
                    module_name, __, output_name = output_spec.partition(".")
                    module = pipeline[module_name]
                    # Check this output is a grouped corpus
                    if not satisfies_typecheck(module.get_output_datatype(output_name)[1], GroupedCorpus()):
                        print("Skipping {}: not a grouped corpus".format(output_spec))
                    else:
                        outputs.append((module_name, output_name))
                        print("Including: {}.{}".format(module_name, output_name))
                else:
                    # Just module name: add all outputs that are grouped corpora
                    module_name = output_spec
                    module = pipeline[module_name]
                    grouped_outputs = [
                        name for name in module.output_names
                        if satisfies_typecheck(module.get_output_datatype(name)[1], GroupedCorpus())
                    ]
                    module_outputs = [(module_name, output) for output in grouped_outputs]
                    if len(module_outputs):
                        print("Including: {}".format(", ".join("{}.{}".format(mn, on) for (mn, on) in module_outputs)))
                        outputs.extend(module_outputs)
                    else:
                        print("No grouped corpus outputs from {}".format(module_name))

        if len(outputs) == 0:
            print("No corpora to convert")

        for module_name, output_name in outputs:
            module = pipeline[module_name]
            try:
                corpus = module.get_output(output_name)
            except DataNotReadyError:
                print("Skipping {}.{} as data is not ready to read".format(module_name, output_name))
            else:
                if not isinstance(corpus, GroupedCorpus.Reader):
                    # This corpus uses a reader other than the standard grouped corpus reader
                    # This probably means it's produced on the fly, or stored some other way
                    # We therefore can't do any kind of conversion
                    print("Skipping {}.{} which reads its data using {}".format(module_name, output_name, type(corpus)))
                elif corpus.uses_tar:
                    # Check the format of the stored data
                    # This is an old tar-based corpus
                    # Look for all the tar files
                    tar_paths = [
                        os.path.join(corpus.data_dir, fn) for fn in corpus.archive_filenames
                    ]
                    if run:
                        print("Converting tar files in {}".format(corpus.data_dir))
                        tar_to_pimarc(tar_paths)
                        # Remove the tar files
                        for tp in tar_paths:
                            os.remove(tp)
                    else:
                        print("Would convert {}.{} from tar to prc".format(module_name, output_name))
                        for tp in tar_paths:
                            print("  {}".format(tp))
                else:
                    print("Already stored using prc: {}.{}".format(module_name, output_name))


def tar_to_pimarc(in_tar_paths):
    for tar_path in in_tar_paths:
        tar_path = os.path.abspath(tar_path)

        # Work out where to put the converted file
        out_filename = "{}.prc".format(os.path.splitext(os.path.basename(tar_path))[0])
        out_path = os.path.join(os.path.dirname(tar_path), out_filename)

        # Create a writer to add files to
        with PimarcWriter(out_path) as arc:
            # Read in the tar file
            tarfile = TarFile.open(tar_path, "r:")
            for tarinfo in tarfile:
                name = tarinfo.name
                with tarfile.extractfile(tarinfo) as tar_member:
                    data = tar_member.read()
                arc.write_file(data, name)
