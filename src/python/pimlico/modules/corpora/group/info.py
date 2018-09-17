# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Group the data points (documents) of an iterable corpus into fixed-size archives.
This is a standard thing to do at the start of the pipeline, since it's a handy
way to store many (potentially small) files without running into filesystem problems.

The documents are simply grouped linearly into a series of groups (archives) such that
each (apart from the last) contains the given number of documents.

After grouping documents in this way, document map modules can be called on the corpus
and the grouping will be preserved as the corpus passes through the pipeline.

.. note::

   This module used to be called ``tar_filter``, but has been renamed in keeping
   with other changes in the new datatype system.

   There also used to be a ``tar`` module that wrote the grouped corpus to disk.
   This has now been removed, since most of the time it's fine to use this
   filter module instead. If you really want to store the grouped corpus, you
   can use the ``store`` module.

"""
import math

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import PimlicoDatatype
from pimlico.datatypes.corpora import IterableCorpus
from pimlico.datatypes.corpora.grouped import GroupedCorpusWithTypeFromInput


class IterableCorpusGrouper(object):
    """
    Tool for grouping documents into archives and naming the archives appropriately.

    Used by `group` module and also by other modules that need to group, or regroup, documents.

    Requires a total number of documents at initialization, but does not depend on this being exactly correct.
    It is used to determine the format of the archive names. It's better to ensure that the given length is an
    overestimate, so the archive names get padded with enough zeroes.

    """
    def __init__(self, archive_size, total_docs, archive_basename="archive"):
        self.archive_basename = archive_basename
        self.total_docs = total_docs
        self.archive_size = archive_size

        # Work out now what the archive names are going to look like
        self.total_archives = int(math.ceil(float(total_docs) / self.archive_size))
        # Work out how many digits to pad the archive numbers with in the filenames
        digits = len("%d" % (self.total_archives-1))
        # Prepare a formatter for archive numbers
        self.archive_name_format = "%s-%%%sd" % (self.archive_basename, "0%d" % digits)

        self.current_archive = 0
        self.current_archive_count = 0
        self.current_archive_name = self.archive_name_format % self.current_archive

    def get_archive_names(self):
        """
        Returns a list of all archive names that will be created, assuming that the given total_docs numbers
        was accurate.
        """
        return [self.archive_name_format % i for i in range(self.total_archives)]

    def next_document(self):
        """
        Move onto the next document and return the archive name for the archive it should be added to.

        """
        # Check whether we've put enough files in the current archive to move onto the next
        if self.current_archive_count == self.archive_size:
            self.current_archive += 1
            self.current_archive_count = 1
            self.current_archive_name = self.archive_name_format % self.current_archive
        else:
            self.current_archive_count += 1
        return self.current_archive_name

    def __iter__(self):
        while True:
            yield self.next_document()


class CorpusGroupReader(PimlicoDatatype.Reader):
    """
    Special reader for grouping documents in an iterable corpus on the fly and
    producing a corresponding grouped corpus.

    """
    class Setup:
        def __init__(self, datatype, input_reader_setup, options):
            self.options = options
            self.input_reader_setup = input_reader_setup
            self.datatype = datatype

        def ready_to_read(self):
            # We're ready when the input's ready
            return self.input_reader_setup.ready_to_read()

    def __init__(self, datatype, setup, pipeline, module=None):
        super(CorpusGroupReader, self).__init__(datatype, setup, pipeline, module=module)
        # Prepare the input reader
        self.input_reader = self.setup.input_reader_setup.get_reader(pipeline, module=module)
        # Create an initial grouper utility to get the list of archive names
        tmp_grouper = IterableCorpusGrouper(self.archive_size, len(self), archive_basename=self.archive_basename)
        self.archives = tmp_grouper.get_archive_names()

    @property
    def metadata(self):
        return self.input_reader.metadata

    def process_setup(self):
        # Don't call the super method: we don't have base dir, etc
        self.archive_basename = self.setup.options["archive_basename"]
        self.archive_size = self.setup.options["archive_size"]

    def __len__(self):
        return len(self.input_reader)

    def extract_file(self, archive_name, filename):
        raise TypeError("cannot extract files from filter: it's not an actual corpus")

    def __iter__(self):
        """
        This is the same as the input reader, since the docs aren't grouped in this case.
        """
        return iter(self.input_reader)

    def doc_iter(self, start_after=None, skip=None, name_filter=None):
        """In this case, just the same as iterating over the input reader"""
        return iter(self)

    def archive_iter(self, start_after=None, skip=None, name_filter=None):
        grouper = IterableCorpusGrouper(self.archive_size, len(self), archive_basename=self.archive_basename)

        skipped = 0
        if start_after is None and skip is None:
            # Don't wait to start
            started = True
        else:
            # Start after we've hit this (archive, doc name), or after we've passed a certain number of docs
            started = False

        for doc_name, doc in self.input_reader:
            # Update the archive name, perhaps moving on to the next one
            archive_name = grouper.next_document()

            # Allow the first portion of the corpus to be skipped
            if not started:
                if start_after == (archive_name, doc_name):
                    # We've hit the condition for starting
                    # Skip this doc and start on the next
                    started = True
                continue

            # Allow the first portion of the corpus to be skipped
            if not started:
                if start_after is not None:
                    # Skip until we get to the requested file + archive
                    if start_after == (archive_name, doc_name):
                        # We've hit the condition for starting
                        # Skip this doc and start on the next (or after we've satisfied "skip")
                        start_after = None
                    continue
                elif skip is not None:
                    if skipped >= skip:
                        # Skipped enough now: stop skipping
                        started = True
                    else:
                        # Keep skipping docs
                        skipped += 1
                        continue
                else:
                    # No more skipping requirements left
                    started = True

            # If subsampling or filtering, decide whether to extract this file
            if name_filter is not None and not name_filter(archive_name, doc_name):
                # Reject this file
                continue

            yield archive_name, doc_name, doc

    def list_archive_iter(self):
        # Since we're not extracting the data here, we can't make things any faster in the case where the document
        #  itself isn't needed. Implement this for compatibility with the normal reader
        for tar_name, doc_name, doc in self.archive_iter():
            yield tar_name, doc_name


class ModuleInfo(BaseModuleInfo):
    module_type_name = "group"
    module_readable_name = "Archive grouper (filter)"
    module_inputs = [("documents", IterableCorpus())]
    module_outputs = [("documents", GroupedCorpusWithTypeFromInput())]
    module_options = {
        "archive_size": {
            "help": "Number of documents to include in each archive (default: 1k)",
            "default": 1000,
            "type": int,
        },
        "archive_basename": {
            "help": "Base name to use for archive tar files. The archive number is appended to this. "
                    "(Default: 'archive')",
            "default": "archive",
        },
    }
    module_executable = False

    def instantiate_output_reader_setup(self, output_name, datatype):
        # We use a special reader to pass documents through from the input
        return CorpusGroupReader.Setup(datatype, self.get_input_reader_setup("documents"), self.options)
