# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Like :mod:`tar <pimlico.modules.corpora.tar>`, but doesn't write the archives to disk. Instead simulates the behaviour of
tar but as a filter, grouping files on the fly and passing them through with an archive name

"""
import math
import random
from collections import OrderedDict

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.corpora import IterableCorpus
from pimlico.datatypes.corpora.grouped import GroupedCorpus, GroupedCorpusWithDataPointTypeFromInput


class IterableCorpusGrouper(object):
    """
    Tool for grouping documents into archives and naming the archives appropriately.

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


# TODO Sort this out in the new system: remove this class and just create a reader instead
# The idea of a filter datatype is not appropriate in the new system
# Use the actual (previously "emulated") datatype as an output type, but create an alternative *reader*
class CorpusGroupFilter(GroupedCorpus):
    emulated_datatype = GroupedCorpus
    datatype_options = OrderedDict([
        ("archive_size", {
            "type": int,
            "default": 1000,
            "help": "Number of documents to group into each archive",
        }),
        ("archive_basename", {
            "default": "archive",
            "help": "First part of the name of each archive. The archive number is appended to this "
                    "to get each archive name",
        }),
    ])

    def __init__(self, input_datatype, **kwargs):
        GroupedCorpus.__init__(self, **kwargs)

        self.archive_basename = self.options["archive_basename"]
        self.archive_size = self.options["archive_size"]
        self.input_datatype = input_datatype

    def data_ready(self, base_dir):
        # We're ready as soon as the input dataset is
        # We need to have been given an input dataset
        return self.input_dataset is not None and self.in

    def __call__(self, *args, **kwargs):
        """
        Override the call so that it takes an input dataset instead of a base dir

        """

    class Reader:
        def __init__(self, *args, **kwargs):
            super(self.__class__, self).__init__(*args, **kwargs)
            self.
    def __len__(self):
        return len(self.input_datatype)

    def extract_file(self, archive_name, filename):
        raise TypeError("cannot extract files from filter: it's not an actual corpus")

    def __iter__(self):
        for __, doc_name, doc in self.archive_iter():
            yield doc_name, doc

    @property
    def tarballs(self):
        if not self.data_ready():
            return []
        return TarredCorpusGrouper(
            self.archive_size, len(self), archive_basename=self.archive_basename).get_archive_names()

    def archive_iter(self, subsample=None, start_after=None, skip=None):
        grouper = TarredCorpusGrouper(self.archive_size, len(self), archive_basename=self.archive_basename)

        if start_after is None:
            # Don't wait to start
            started = True
        else:
            # Start after we've hit this (archive, doc name)
            started = False

        # Pass through the raw_data attribute to the input corpus before we start iterating
        self.input_datatype.raw_data = self.raw_data

        for doc_name, doc in self.input_datatype:
            # Update the archive name, perhaps moving on to the next one
            archive_name = grouper.next_document()

            # Allow the first portion of the corpus to be skipped
            if not started:
                if start_after == (archive_name, doc_name):
                    # We've hit the condition for starting
                    # Skip this doc and start on the next
                    started = True
                continue

            # If subsampling, decide whether to extract this file
            if subsample is not None and random.random() > subsample:
                # Reject this file
                continue

            yield archive_name, doc_name, doc

    def list_archive_iter(self):
        # Since we're not extracting the data here, we can't make things any faster in the case where the document
        #  itself isn't needed. Implement this for compatibility with TarredCorpus
        for tar_name, doc_name, doc in self.archive_iter():
            yield tar_name, doc_name

    def data_ready(self):
        return self.input_datatype.data_ready()


class ModuleInfo(BaseModuleInfo):
    module_type_name = "group_filter"
    module_readable_name = "Archive grouper (filter)"
    module_inputs = [("documents", IterableCorpus())]
    module_outputs = [("documents", GroupedCorpusWithDataPointTypeFromInput())]
    module_options = {
        "archive_size": {
            "help": "Number of documents to include in each archive (default: 1k)",
            "default": 1000,
        },
        "archive_basename": {
            "help": "Base name to use for archive tar files. The archive number is appended to this. "
                    "(Default: 'archive')",
            "default": "archive",
        },
    }
    module_executable = False

    def instantiate_output_reader(self, output_name, datatype, base_dir):
        # TODO Create a custom reader and instantiate it here
