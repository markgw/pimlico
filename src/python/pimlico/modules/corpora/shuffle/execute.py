from __future__ import division

from future import standard_library

from pimlico.datatypes import GroupedCorpus
from pimlico.utils.pimarc import PimarcReader
from pimlico.utils.pimarc.reader import read_doc_from_pimarc

standard_library.install_aliases()

from numpy import random

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.modules.corpora.group.info import IterableCorpusGrouper
from pimlico.utils.progress import get_progress_bar


class ModuleExecutor(BaseModuleExecutor):
    def execute(self):
        input_corpus = self.info.get_input("corpus")
        archive_basename = self.info.options["archive_basename"]
        rng_seed = self.info.options["seed"]

        # Check that the input is stored in the pipeline-internal format, not
        #  dynamically produced. This check would be better done at the level
        #  of datatypes, but for now we enforce it here
        if not type(input_corpus) is GroupedCorpus.Reader:
            # Uses some other reader, so we don't know that it's suitably stored for random access
            raise TypeError("input corpus to be randomly shuffled is not stored at a pipeline-internal "
                            "corpus, so can't be randomly accessed. Consider using the 'shuffle_linear' "
                            "module type instead")
        if input_corpus.uses_tar:
            raise TypeError("input corpus is stored using the old tar format. Re-run the module that "
                            "produced this output to get it in pimarc format (or use the 'shuffle_linear' "
                            "module)")
        self.log.info("Shuffling {:,d} documents from input corpus".format(len(input_corpus)))

        # Prepare an index of all the documents, as archive ids and doc ids
        # Use IDs instead of names to improve memory efficiency with large corpora
        archive_filenames = input_corpus.archive_filenames
        # Read the index for each archive to check where each file's data starts
        self.log.info("Reading in document indices")
        archive_doc_starts = [
            (archive_num, metadata_start) for (archive_num, archive_filename) in enumerate(archive_filenames)
            for (metadata_start, data_start) in PimarcReader(archive_filename).index.filenames.values()
        ]
        self.log.info("Shuffling documents")
        # Seed the RNG
        random.seed(rng_seed)
        # Shuffle these indices in place to get their order in the output corpus
        random.shuffle(archive_doc_starts)

        self.log.info("Writing randomly shuffled output corpus")
        # Check the max length of an archive
        max_archive_size = max(len(PimarcReader(archive_filename).index) for archive_filename in archive_filenames)
        with self.info.get_output_writer("corpus") as writer:
            grouper = IterableCorpusGrouper(max_archive_size, len(input_corpus), archive_basename=archive_basename)
            # Iterate over each bin in turn
            pbar = get_progress_bar(len(archive_doc_starts), title="Writing")
            for archive_num, metadata_start in pbar(archive_doc_starts):
                metadata, data = read_doc_from_pimarc(archive_filenames[archive_num], metadata_start)

                archive_name = grouper.next_document()
                # Add this document to the end of the output corpus
                writer.add_document(archive_name, metadata["name"], data, metadata=metadata)
