# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Simple filter to truncate a dataset after a given number of documents, potentially offsetting by a number
of documents. Mainly useful for creating small subsets of a corpus for testing a pipeline before running
on the full corpus.

Can be run on an iterable corpus or a tarred corpus. If the input is a tarred corpus, the filter will
emulate a tarred corpus with the appropriate datatype, passing through the archive names from the input.

"""
from itertools import islice

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes.base import IterableCorpus, DynamicOutputDatatype, \
    iterable_corpus_with_data_point_type, InvalidDocument
from pimlico.datatypes.tar import TarredCorpus, tarred_corpus_with_data_point_type


class CorpusSubsetFilter(IterableCorpus):
    def __init__(self, pipeline, input_datatype, size, offset=0, skip_invalid=False):
        IterableCorpus.__init__(self, None, pipeline)

        self.skip_invalid = skip_invalid
        self.offset = offset
        self.input_datatype = input_datatype
        self.size = size

        self.data_point_type = self.input_datatype.data_point_type
        self._num_valid_docs = None

    def __len__(self):
        if self.skip_invalid:
            return min(self.size, self.num_valid_docs)
        else:
            return min(self.size, len(self.input_datatype))

    @property
    def num_valid_docs(self):
        if self._num_valid_docs is None:
            self._num_valid_docs = sum(1 for doc, doc_name in self.input_datatype
                                       if not isinstance(doc, InvalidDocument))
        return self._num_valid_docs

    def __iter__(self):
        return islice(self.input_datatype, self.offset, self.offset+self.size)

    def data_ready(self):
        return True


class TarredCorpusSubsetFilter(TarredCorpus):
    def __init__(self, pipeline, input_datatype, size, offset=0, skip_invalid=False, **kwargs):
        TarredCorpus.__init__(self, None, pipeline, **kwargs)

        self.skip_invalid = skip_invalid
        self.offset = offset
        self.input_datatype = input_datatype
        self.size = size

        self.data_point_type = self.input_datatype.data_point_type
        self._num_valid_docs = None

    def __len__(self):
        if self.skip_invalid:
            return min(self.size, self.num_valid_docs)
        else:
            return min(self.size, len(self.input_datatype))

    @property
    def num_valid_docs(self):
        if self._num_valid_docs is None:
            self._num_valid_docs = sum(1 for doc, doc_name in self.input_datatype
                                       if not isinstance(doc, InvalidDocument))
        return self._num_valid_docs

    def archive_iter(self, subsample=None, start_after=None, skip=None):
        skip = skip or 0
        start_index = self.offset + min(skip, self.size)
        end_index = self.offset + self.size

        if subsample is not None:
            raise NotImplementedError("tarred corpus subset filter doesn't implement subsampling")

        # We can't use the base datatype's start_after functionality, as we don't know how many docs it's skipped
        # Have to implement it here instead
        started = start_after is None
        for doc_num, (archive, doc_name, doc) in enumerate(self.input_datatype.archive_iter()):
            if start_after is not None and not started and (archive, doc_name) == start_after:
                started = True
                # Don't yield this one: start from the next one (unless we're still skipping)
                continue
            if doc_num < start_index:
                # Skip this doc
                continue
            if doc_num >= end_index:
                # Reached the end of the slice: stop altogether
                return
            # We're in the right range: pass through the doc
            yield archive, doc_name, doc

    def data_ready(self):
        return True


class DataPointTypeFromInput(DynamicOutputDatatype):
    """
    Infer output corpus' data-point type from the type of an input.
    Passes the type through, except where the input datatype provides an `emulated_datatype`.

    If the input is a tarred corpus, so is the output. Otherwise, it's just an IterableCorpus.

    Input name may be given. Otherwise, the default input is used.

    """
    datatype_name = "corpus with data-point from input"

    def __init__(self, input_name=None):
        self.input_name = input_name

    def get_datatype(self, module_info):
        datatype = module_info.get_input_datatype(self.input_name)
        # If the input datatype emulates another, it is that other that we will produce as output
        if datatype.emulated_datatype is not None:
            datatype = datatype.emulated_datatype
        # Check whether the input was a tarred corpus
        if issubclass(datatype, TarredCorpus):
            return tarred_corpus_with_data_point_type(datatype.data_point_type)
        else:
            return iterable_corpus_with_data_point_type(datatype.data_point_type)


class ModuleInfo(BaseModuleInfo):
    module_type_name = "subset"
    module_readable_name = "Corpus subset"
    module_inputs = [("documents", IterableCorpus)]
    module_outputs = [("documents", DataPointTypeFromInput())]
    module_options = {
        "size": {
            "help": "Number of documents to include",
            "required": True,
            "type": int,
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
    module_executable = False

    def instantiate_output_datatype(self, output_name, output_datatype):
        if issubclass(output_datatype, TarredCorpus):
            return TarredCorpusSubsetFilter(self.pipeline, self.get_input("documents"),
                                            self.options["size"], offset=self.options["offset"],
                                            skip_invalid=self.options["skip_invalid"])
        else:
            return CorpusSubsetFilter(self.pipeline, self.get_input("documents"),
                                      self.options["size"], offset=self.options["offset"],
                                      skip_invalid=self.options["skip_invalid"])
