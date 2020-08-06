# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Interleave data points from two (or more) corpora to produce a bigger corpus.

Similar to :mod:`~pimlico.modules.corpora.concat`, but interleaves the documents
when iterating. Preserves the order of documents within corpora and takes
documents two each corpus in inverse proportion to its length, i.e. spreads
out a smaller corpus so we don't finish iterating over it earlier than
the longer one.

They must have the same data point type, or one must be a subtype of the other.

In theory, we could find the most specific common ancestor and use that as the output type, but this is
not currently implemented and may not be worth the trouble. Perhaps we will add this in future.

"""
from builtins import zip
from builtins import next
from builtins import object

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import MultipleInputs
from pimlico.datatypes.corpora import GroupedCorpus, IterableCorpus
from pimlico.datatypes.corpora.grouped import GroupedCorpusWithTypeFromInput
from pimlico.modules.corpora.group.info import IterableCorpusGrouper


class ModuleInfo(BaseModuleInfo):
    module_type_name = "interleave"
    module_readable_name = "Interleaved corpora"
    module_inputs = [("corpora", MultipleInputs(GroupedCorpus()))]
    module_outputs = [("corpus", GroupedCorpusWithTypeFromInput())]
    module_executable = False
    module_options = {
        "archive_size": {
            "help": "Documents are regrouped into new archives. "
                    "Number of documents to include in each archive (default: 1k)",
            "default": 1000,
        },
        "archive_basename": {
            "help": "Documents are regrouped into new archives. "
                    "Base name to use for archive tar files. The archive number is appended to this. "
                    "(Default: 'archive')",
            "default": "archive",
        },
    }
    module_supports_python2 = True

    def instantiate_output_reader_setup(self, output_name, datatype):
        return InterleavedGroupedCorpusReader.Setup(
            self.get_output_datatype("corpus")[1],
            self.get_input_reader_setup("corpora", always_list=True),
            self.options["archive_size"], self.options["archive_basename"]
        )


class InterleavedGroupedCorpusReader(GroupedCorpus.Reader):
    """
    A custom reader that is used for the output of the interleave module.

    This simply wraps the input corpora to provide iteration over the two (or more)
    interleaved.

    """
    metadata = {}

    def __init__(self, datatype, setup, pipeline, **kwargs):
        # Don't call GroupedCorpus init, but jump up to IterableCorpus
        IterableCorpus.Reader.__init__(self, datatype, setup, pipeline, **kwargs)
        # Get readers for each of the input corpora
        self.input_readers = [
            setup.get_reader(self.pipeline, module=self.module) for setup in self.setup.input_reader_setups
        ]
        self.archive_grouper = IterableCorpusGrouper(
            self.setup.archive_size, len(self), archive_basename=self.setup.archive_basename
        )
        # These are the actual archive names we'll use
        self.archives = self.archive_grouper.get_archive_names()
        # Pretend we've got archive filenames
        self.archive_filenames = self.archives

    def __len__(self):
        return sum((len(reader) for reader in self.input_readers), 0)

    def extract_file(self, archive_name, filename):
        raise NotImplementedError("cannot extract file from interleaved corpora")

    def _iter_docs(self, name_filter=None):
        lengths = [len(c) for c in self.input_readers]
        # The longest corpus increments its progress count by 1 for each document
        # Shorter ones increment theirs by proportionally less
        # Then we always just yield a document from the corpus with the lowest progress
        # The result is that we get documents more often from the longer corpus
        doc_weights = [float(max(lengths))/float(l) if l>0 else 0. for l in lengths]
        progresses = [0. for _ in self.input_readers]
        # If a corpus has 0 docs, mark it as finished already from the start
        finished = [l == 0 for l in lengths]
        iterators = [c.archive_iter(name_filter=name_filter) for c in self.input_readers]

        while not all(finished):
            # Take a document from the corpus with lowest progress count
            # Takes the first in the case of ties
            next_corpus = min((prog, i) for (i, prog) in enumerate(progresses) if not finished[i])[1]
            try:
                # We ignore this archive name, since we're regrouping
                archive_name, doc_name, doc = next(iterators[next_corpus])
            except StopIteration:
                # Reached the end of this corpus
                # Mark as finished, so we stop trying to take from this one
                finished[next_corpus] = True
            else:
                # Distinguish the doc name so we can see what corpus it came from
                doc_name = "corp{}_{}".format(next_corpus, doc_name)
                yield doc_name, doc
            # Increment this corpus' progress
            progresses[next_corpus] += doc_weights[next_corpus]

    def archive_iter(self, start_after=None, skip=None, name_filter=None):
        skipped = 0
        if start_after is None and skip is None:
            # Don't wait to start
            started = True
        else:
            # Start after we've hit this (archive, doc name), or after we've passed a certain number of docs
            started = False

        # We regrouped docs into archives, using a new set of archive names, since it
        # doesn't make sense to use those in the input when interleaving
        for archive_name, (doc_name, doc) in zip(self.archive_grouper, self._iter_docs(name_filter=name_filter)):
            if not started:
                if start_after is not None:
                    if start_after == (archive_name, doc_name):
                        # Reached the starting doc
                        start_after = None
                    else:
                        # Still waiting for the starting doc
                        continue
                if skip is not None:
                    if skipped < skip:
                        skipped += 1
                        continue
                # Not skipping any more
                started = True
            yield archive_name, doc_name, doc

    def list_archive_iter(self):
        for archive, doc_name, doc in self.archive_iter():
            yield archive, doc_name

    class Setup(object):
        def __init__(self, datatype, input_reader_setups, archive_size, archive_basename):
            self.archive_basename = archive_basename
            self.archive_size = archive_size
            self.input_reader_setups = input_reader_setups
            self.datatype = datatype

        def ready_to_read(self):
            return all(setup.ready_to_read() for setup in self.input_reader_setups)

    def process_setup(self):
        # Override to not do data path processing
        return
