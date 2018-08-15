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

.. todo::

   Update to new datatypes system and add test pipeline

"""
from itertools import izip

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import DynamicOutputDatatype, MultipleInputs
from pimlico.datatypes.tar import TarredCorpus, tarred_corpus_with_data_point_type
from pimlico.modules.corpora.tar_filter.info import TarredCorpusGrouper
from ..concat.info import _common_data_point_type


class TarredCorpusInterleaveFilter(TarredCorpus):
    def __init__(self, pipeline, input_datatypes, archive_size=1000, archive_basename="archive", **kwargs):
        self.archive_size = archive_size
        self.archive_basename = archive_basename
        self._master_raw_data = False
        self.input_datatypes = input_datatypes
        TarredCorpus.__init__(self, None, pipeline, **kwargs)

    def __len__(self):
        return sum((len(d) for d in self.input_datatypes), 0)

    def _set_raw_data(self, val):
        self._master_raw_data = val
        # Set on all the datasets
        for d in self.input_datatypes:
            d.raw_data = val
    def _get_raw_data(self):
        return self._master_raw_data
    raw_data = property(_get_raw_data, _set_raw_data)

    def extract_file(self, archive_name, filename):
        raise NotImplementedError("cannot extract file from concatenation of corpora")

    def _iter_docs(self, subsample=None):
        lengths = [len(c) for c in self.input_datatypes]
        # The longest corpus increments its progress count by 1 for each document
        # Shorter ones increment theirs by proportionally less
        # Then we always just yield a document from the corpus with the lowest progress
        # The result is that we get documents more often from the longer corpus
        doc_weights = [float(max(lengths))/float(l) for l in lengths]
        progresses = [0. for _ in self.input_datatypes]
        finished = [False for _ in self.input_datatypes]
        iterators = [c.archive_iter(subsample=subsample) for c in self.input_datatypes]

        while not all(finished):
            # Take a document from the corpus with lowest progress count
            # Takes the first in the case of ties
            next_corpus = min((prog, i) for (i, prog) in enumerate(progresses) if not finished[i])[1]
            try:
                # We ignore this archive name, since we're regrouping
                archive_name, doc_name, doc = iterators[next_corpus].next()
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

    def archive_iter(self, subsample=None, start_after=None, skip=None):
        skipped = 0
        if start_after is None and skip is None:
            # Don't wait to start
            started = True
        else:
            # Start after we've hit this (archive, doc name), or after we've passed a certain number of docs
            started = False
            # Don't allow subsample to be used together with start_after or skip, as their interaction is tricky!
            if subsample is not None:
                raise ValueError("corpus concat does not permit combining the 'subsample' option with 'start_after' "
                                 "or 'skip'")

        # We regrouped docs into archives, using a new set of archive names, since it
        # doesn't make sense to use those in the input when interleaving
        archive_grouper = TarredCorpusGrouper(self.archive_size, len(self), archive_basename=self.archive_basename)
        for archive_name, (doc_name, doc) in izip(archive_grouper, self._iter_docs()):
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
        # Can't easily make this faster than iterating
        for archive_name, doc_name, doc in self.archive_iter():
            yield archive_name, doc_name

    def data_ready(self):
        return all(d.data_ready() for d in self.input_datatypes)


def tarred_corpus_interleave_filter_dp_type(dp_type):
    class TarredCorpusInterleaveFilterSubtype(TarredCorpusInterleaveFilter):
        data_point_type = dp_type
    return TarredCorpusInterleaveFilterSubtype


class DataPointTypeFromInputs(DynamicOutputDatatype):
    """
    Infer output corpus' data-point type from the type of an input.
    Passes the type through, except where the input datatype provides an `emulated_datatype`.

    Input name may be given. Otherwise, the default input is used.

    """
    datatype_name = "corpus with data-point from input"

    def __init__(self, input_name=None):
        self.input_name = input_name

    def get_datatype(self, module_info):
        datatypes = module_info.get_input_datatype(self.input_name, always_list=True)
        # If the input datatype emulates another, it is that other that we will produce as output
        datatypes = [datatype.emulated_datatype or datatype for datatype in datatypes]
        # Find the common data point type to use for the output
        dp_type = _common_data_point_type([d.data_point_type for d in datatypes])

        return tarred_corpus_with_data_point_type(dp_type)


class ModuleInfo(BaseModuleInfo):
    module_type_name = "concat"
    module_readable_name = "Corpus concatenation"
    module_inputs = [("corpora", MultipleInputs(TarredCorpus))]
    module_outputs = [("corpus", DataPointTypeFromInputs())]
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

    def instantiate_output_datatype(self, output_name, output_datatype, **kwargs):
        datatypes = self.get_input("corpora", always_list=True)
        # Find the common datapoint type to use for the output corpus
        dp_type = _common_data_point_type([d.data_point_type for d in datatypes])
        filter_type = tarred_corpus_interleave_filter_dp_type(dp_type)

        return filter_type(self.pipeline, datatypes,
                           archive_size=self.options["archive_size"], archive_basename=self.options["archive_basename"],
                           module=self)
