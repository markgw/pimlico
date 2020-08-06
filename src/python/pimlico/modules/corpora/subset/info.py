# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Simple filter to truncate a dataset after a given number of documents, potentially offsetting by a number
of documents. Mainly useful for creating small subsets of a corpus for testing a pipeline before running
on the full corpus.

Can be run on an iterable corpus or a tarred corpus. If the input is a tarred corpus, the filter will
emulate a tarred corpus with the appropriate datatype, passing through the archive names from the input.

When a number of valid documents is required (calculating corpus length when skipping invalid docs),
if one is stored in the metadata as ``valid_documents``, that count is used instead of iterating
over the data to count them up.

"""
from builtins import object

from itertools import islice

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes.corpora import IterableCorpus, is_invalid_doc, GroupedCorpus
from pimlico.datatypes.corpora.grouped import CorpusWithTypeFromInput
from pimlico.utils.core import cached_property


class ModuleInfo(BaseModuleInfo):
    module_type_name = "subset"
    module_readable_name = "Corpus subset"
    module_inputs = [("corpus", IterableCorpus())]
    module_outputs = [("corpus", CorpusWithTypeFromInput())]
    module_executable = False
    module_options = {
        "size": {
            "help": "Number of documents to include",
            "required": True,
            "type": int,
            "example": "100",
        },
        "offset": {
            "help": "Number of documents to skip at the beginning of the corpus (default: 0, start at beginning)",
            "default": 0,
            "type": int,
        },
        "skip_invalid": {
            "help": "Skip over any invalid documents so that the output subset contains the chosen number of (valid) "
                    "documents (or as many as possible) and no invalid ones. By default, invalid documents are passed "
                    "through and counted towards the subset size",
            "type": str_to_bool,
        },
    }
    module_supports_python2 = True

    def instantiate_output_reader_setup(self, output_name, datatype):
        if isinstance(datatype, GroupedCorpus):
            # Produce reader with GroupedCorpus.Reader interface
            Setup = SubsetGroupedCorpusReader.Setup
        else:
            # Produce reader that just acts like an IterableCorpus
            Setup = SubsetIterableCorpusReader.Setup

        return Setup(self.get_output_datatype("corpus")[1], self.get_input_reader_setup("corpus"), self.options)


class SubsetIterableCorpusReader(IterableCorpus.Reader):
    """
    A custom reader that is used for the output of the subset module.

    This version is used where the input corpus is not a grouped corpus. It
    implements the interface of IterableCorpus' reader, but not GroupedCorpus.

    """
    metadata = {}

    class Setup(object):
        def __init__(self, datatype, input_reader_setup, options):
            self.datatype = datatype
            self.options = options
            self.input_reader_setup = input_reader_setup

        def ready_to_read(self):
            # We're ready when the input's ready
            return self.input_reader_setup.ready_to_read()

    def __init__(self, datatype, setup, pipeline, **kwargs):
        # Don't call GroupedCorpus init, but jump up to IterableCorpus
        IterableCorpus.Reader.__init__(self, datatype, setup, pipeline, **kwargs)
        # Get reader for the input corpus
        self.input_reader = self.setup.input_reader_setup.get_reader(self.pipeline, module=self.module)
        # Get the options
        self.size = self.setup.options["size"]
        self.offset = self.setup.options["offset"]
        self.skip_invalid = self.setup.options["skip_invalid"]

    def __len__(self):
        return self.length

    @cached_property
    def length(self):
        if self.skip_invalid:
            # If we have as many as `size` docs, we can stop counting
            return sum(islice(
                (1 for doc_name, doc in self.input_reader if not is_invalid_doc(doc)),
                self.offset, self.offset+self.size
            ))
        else:
            # If not skipping invalid docs, it's easier to work out the output size
            return min(self.size, len(self.input_reader) - self.offset)

    def __iter__(self):
        if self.skip_invalid:
            doc_iter = ((doc_name, doc) for (doc_name, doc) in self.input_reader if not is_invalid_doc(doc))
        else:
            doc_iter = iter(self.input_reader)
        return islice(doc_iter, self.offset, self.offset+self.size)

    def process_setup(self):
        # Override to not do data path processing
        return


class SubsetGroupedCorpusReader(SubsetIterableCorpusReader):
    """
    A custom reader that is used for the output of the subset module.

    This simply wraps the input corpus to provide iteration over the truncated version.

    """
    metadata = {}

    def __init__(self, datatype, setup, pipeline, **kwargs):
        SubsetIterableCorpusReader.__init__(self, datatype, setup, pipeline, **kwargs)
        # Provide the same interface to archives as the GroupedCorpus reader
        # Just pass through archive names
        # Note that some might not ever be used
        self.archive_filenames = self.input_reader.archive_filenames
        self.archives = self.input_reader.archives

    def extract_file(self, archive_name, filename):
        return self.input_reader.extract_file(archive_name, filename)

    def archive_iter(self, start_after=None, skip=None, name_filter=None):
        if skip is not None and skip < 1:
            skip = None
        # We use the input's skip functionality to skip over the offset
        # We then have to implement our own skip functionality (and start_after), so that skipped docs
        #  count towards the subset
        started = start_after is None or skip is None
        skipped = 0
        done = 0
        for doc_num, (archive, doc_name, doc) in enumerate(self.input_reader.archive_iter(skip=self.offset)):
            if done >= self.size:
                # Reached the end of the slice: stop iterating
                return

            if self.skip_invalid and is_invalid_doc(doc):
                # Jump over invalid docs
                # These don't count towards the subset size
                continue

            done += 1

            if not started:
                if start_after is not None:
                    if (archive, doc_name) == start_after:
                        # Start on the next doc
                        start_after = None
                    continue
                elif skip is not None:
                    if skipped < skip:
                        skipped += 1
                        continue
                    else:
                        started = True

            # If filtering, decide whether to include this file
            if name_filter is not None and not name_filter(archive, doc_name):
                # Reject this file
                continue

            # We're in the right range: pass through the doc
            yield archive, doc_name, doc

    def list_archive_iter(self):
        if self.skip_invalid:
            # Can't make this faster than reading all, as we have to check whether they're invalid
            return ((archive, doc_name) for (archive, doc_name, doc) in self.archive_iter())
        else:
            return islice(self.input_reader.list_archive_iter(), self.offset, self.offset+self.size)
