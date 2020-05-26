from __future__ import division
from future import standard_library

from pimlico.utils.pimarc import PimarcWriter, PimarcReader

standard_library.install_aliases()
from builtins import range

import io
import math
import os
import tarfile
from numpy import random
import shutil

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.modules.corpora.group.info import IterableCorpusGrouper
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_corpus = self.info.get_input("corpus")
        self.log.info("Reading {:,d} documents from input corpus".format(len(input_corpus)))

        bin_size = self.info.options["bin_size"]
        keep_archive_names = self.info.options["keep_archive_names"]
        num_bins = self.info.options["num_bins"]
        archive_basename = self.info.options["archive_basename"]

        if num_bins is None:
            # Normal behaviour: calculate num bins from bin size
            num_bins = int(math.ceil(float(len(input_corpus)) / bin_size))
        # Recompute the expected bin size from the number of bins
        bin_size = len(input_corpus) // num_bins
        self.log.info("Storing documents in {:,} temporary bins with expected size {:,}".format(num_bins, bin_size))

        # Create a directory for our temporary bins
        temp_dir = os.path.join(self.info.get_absolute_output_dir("corpus"), "bins")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        # Work out how many digits to pad the archive numbers with in the filenames
        digits = len("%d" % (num_bins-1))
        # Prepare a formatter for archive numbers
        bin_name_format = "bin-{{:0{}d}}.prc".format(digits)

        # Open a pimarc for each bin to write documents out
        bin_filenames = [os.path.join(temp_dir, bin_name_format.format(i)) for i in range(num_bins)]
        bin_writers = [PimarcWriter(fn) for fn in bin_filenames]

        # Iterate over all input documents, storing them in the bins
        self.log.info("Shuffling docs into temporary bins in {}".format(temp_dir))
        # While reading, track the maximum archive size and use that as archive size later
        max_archive_size = 0
        archive_size = 0
        prev_archive = None

        pbar = get_progress_bar(len(input_corpus), title="Shuffling")
        for archive, doc_name, doc in pbar(input_corpus.archive_iter()):
            if archive != prev_archive:
                archive_size = 1
                prev_archive = archive
                max_archive_size = max(max_archive_size, archive_size)
            else:
                archive_size += 1

            if keep_archive_names:
                doc_name = "{}__{}".format(archive, doc_name)
            # Choose a bin at random
            bin = random.randint(0, num_bins)
            # Get the document's raw data
            data = doc.raw_data
            metadata = doc.metadata

            # Append the document to a bin
            bin_writers[bin].write_file(data, doc_name, metadata=metadata)

        max_archive_size = max(max_archive_size, archive_size)

        self.log.info("Detected archive size of {:,} from input corpus".format(max_archive_size))

        with self.info.get_output_writer("corpus") as writer:
            self.log.info("Shuffling bins and writing output corpus to {}".format(writer.data_dir))
            grouper = IterableCorpusGrouper(max_archive_size, len(input_corpus), archive_basename=archive_basename)
            # Iterate over each bin in turn
            pbar = get_progress_bar(len(bin_filenames), title="Processing bins")
            for bin_fn in pbar(bin_filenames):
                bin_reader = PimarcReader(bin_fn)
                # Shuffle randomly within the bin, as they're currently
                # just in the order we read them from the input corpus
                bin_doc_list = list(bin_reader.index.filenames.keys())
                random.shuffle(bin_doc_list)

                for doc_name in bin_doc_list:
                    archive_name = grouper.next_document()
                    metadata, raw_data = bin_reader[doc_name]
                    # Add this document to the end of the output corpus
                    writer.add_document(archive_name, doc_name, raw_data, metadata=metadata)

        # Remove the bins dir
        shutil.rmtree(temp_dir)
