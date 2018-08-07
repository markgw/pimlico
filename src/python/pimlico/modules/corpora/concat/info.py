# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Concatenate two (or more) corpora to produce a bigger corpus.

They must have the same data point type, or one must be a subtype of the other.

"""
from itertools import chain

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import MultipleInputs
from pimlico.datatypes.corpora import IterableCorpus, GroupedCorpus
from pimlico.datatypes.corpora.grouped import CorpusWithTypeFromInput


class ModuleInfo(BaseModuleInfo):
    module_type_name = "concat"
    module_readable_name = "Corpus concatenation"
    module_inputs = [("corpora", MultipleInputs(IterableCorpus()))]
    module_outputs = [("corpus", CorpusWithTypeFromInput())]
    module_executable = False

    def instantiate_output_reader_setup(self, output_name, datatype):
        if isinstance(datatype, GroupedCorpus):
            # Produce reader with GroupedCorpus.Reader interface
            Setup = ConcatenatedGroupedCorpusReader.Setup
        else:
            # Produce reader that just acts like an IterableCorpus
            Setup = ConcatenatedIterableCorpusReader.Setup

        return Setup(
            self.get_output_datatype("corpus")[1],
            self.get_input_reader_setup("corpora", always_list=True),
        )


class ConcatenatedGroupedCorpusReader(GroupedCorpus.Reader):
    """
    A custom reader that is used for the output of the concatenate module.

    This simply wraps the input corpora to provide iteration over the two (or more)
    in sequence.

    """
    metadata = {}

    def __init__(self, datatype, setup, pipeline, **kwargs):
        # Don't call GroupedCorpus init, but jump up to IterableCorpus
        IterableCorpus.Reader.__init__(self, datatype, setup, pipeline, **kwargs)
        # Get readers for each of the input corpora
        self.input_readers = [
            setup.get_reader(self.pipeline, module=self.module) for setup in self.setup.input_reader_setups
        ]
        # To make sure we don't reuse archive names, add a prefix to each corpus' archive names
        self.corpus_prefixes = ["corpus{}_".format(i) for i in range(len(self.input_readers))]
        # Provide the same interface to archives as the GroupedCorpus reader
        # These aren't real filenames, but provide something
        self.archive_filenames = [
            "{}{}".format(prx, fn)
            for (prx, reader) in zip(self.corpus_prefixes, self.input_readers)
            for fn in reader.archive_filenames
        ]
        # These are the actual archive names we'll use
        self.archives = [
            "{}{}".format(prx, archive)
            for (prx, reader) in zip(self.corpus_prefixes, self.input_readers) for archive in reader.archives
        ]
        # Make it easy to trace an archive name back to the original corpus later
        self.archive_name_map = dict(
            ("{}{}".format(prx, old_archive_name), (reader, old_archive_name))
            for (prx, reader) in zip(self.corpus_prefixes, self.input_readers) for old_archive_name in reader.archives
        )

    def __len__(self):
        return sum((len(reader) for reader in self.input_readers), 0)

    def extract_file(self, archive_name, filename):
        # Trace the archive back to the input readers and pass over to them to get the file
        reader, old_archive_name = self.archive_name_map[archive_name]
        return reader.extract_file(old_archive_name, filename)

    def archive_iter(self, start_after=None, skip=None, name_filter=None):
        skipped = 0
        if start_after is None and skip is None:
            # Don't wait to start
            started = True
        else:
            # Start after we've hit this (archive, doc name), or after we've passed a certain number of docs
            started = False

        for corpus_num, reader in enumerate(self.input_readers):
            corpus_prefix = u"corpus{}_".format(corpus_num)

            if not started:
                if start_after is not None:
                    # Check whether the archive name uses this corpus prefix
                    if not start_after[0].startswith(corpus_prefix):
                        # Waiting for a particular archive, but it's not in this corpus, so skip to the next
                        continue
                    else:
                        # The starting archive is somewhere in this dataset
                        start_archive = start_after[0][len(corpus_prefix):]
                        dataset_iter = reader.archive_iter(start_after=(start_archive, start_after[1]))
                        start_after = None
                elif skip is not None and skip - skipped > len(reader):
                    # If we've still got more left to skip than are in this corpus, we can skip the whole thing
                    skipped += len(reader)
                    continue
                else:
                    dataset_iter = reader.archive_iter()
            else:
                dataset_iter = reader.archive_iter()

            if skip is not None:
                # If we've still got some to skip, do so by iterating over the corpus
                # It's possible there won't be enough left in the corpus (after start_after) to skip
                try:
                    while skip - skipped > 0:
                        dataset_iter.next()
                        skipped += 1
                except StopIteration:
                    pass
                if skip - skipped == 0:
                    skip = None
                    started = True
                else:
                    # Reached end of corpus without exhausting skip
                    continue

            for archive_name, doc_name, doc in dataset_iter:
                started = True
                yield u"{}{}".format(corpus_prefix, archive_name), doc_name, doc

    def list_archive_iter(self):
        for corpus_num, reader in enumerate(self.input_readers):
            corpus_prefix = "corpus{}_".format(corpus_num)
            for archive_name, doc_name in reader.list_archive_iter():
                yield u"{}{}".format(corpus_prefix, archive_name), doc_name

    class Setup:
        def __init__(self, datatype, input_reader_setups):
            self.input_reader_setups = input_reader_setups
            self.datatype = datatype

        def ready_to_read(self):
            return all(setup.ready_to_read() for setup in self.input_reader_setups)

    def process_setup(self):
        # Override to not do data path processing
        return


class ConcatenatedIterableCorpusReader(IterableCorpus.Reader):
    """
    A custom reader that is used for the output of the concatenate module.

    This version is used where not all the input corpora are grouped corpora. It
    implements the interface of IterableCorpus' reader, but not GroupedCorpus.

    """
    metadata = {}

    def __init__(self, datatype, setup, pipeline, **kwargs):
        # Don't call GroupedCorpus init, but jump up to IterableCorpus
        IterableCorpus.Reader.__init__(self, datatype, setup, pipeline, **kwargs)
        # Get readers for each of the input corpora
        self.input_readers = [
            setup.get_reader(self.pipeline, module=self.module) for setup in self.setup.input_reader_setups
        ]
        # To make sure we don't reuse archive names, add a prefix to each corpus' archive names
        self.corpus_prefixes = ["corpus{}_".format(i) for i in range(len(self.input_readers))]

    def __len__(self):
        return sum((len(reader) for reader in self.input_readers), 0)

    def __iter__(self):
        return chain(*self.input_readers)

    class Setup:
        def __init__(self, datatype, input_reader_setups):
            self.input_reader_setups = input_reader_setups
            self.datatype = datatype

        def ready_to_read(self):
            return all(setup.ready_to_read() for setup in self.input_reader_setups)

    def process_setup(self):
        # Override to not do data path processing
        return
