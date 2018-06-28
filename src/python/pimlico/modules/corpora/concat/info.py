# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Concatenate two corpora to produce a bigger corpus.

They must have the same data point type, or one must be a subtype of the other.

In theory, we could find the most specific common ancestor and use that as the output type, but this is
not currently implemented and may not be worth the trouble. Perhaps we will add this in future.

"""
from itertools import islice, chain

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.base import IterableCorpus, DynamicOutputDatatype, \
    iterable_corpus_with_data_point_type, MultipleInputs
from pimlico.old_datatypes.tar import TarredCorpus, tarred_corpus_with_data_point_type


def _common_data_point_type(types):
    # Simplest case: all identical
    if all(t is types[0] for t in types[1:]):
        return types[0]
    # Otherwise, check for each one whether all the others are subtypes
    for t in types:
        if all(issubclass(t1, t) for t1 in types):
            return t
    # No type to serve as the common type
    raise TypeError("incompatible data point types for concatenation: %s" % ", ".join(t.__name__ for t in types))


class CorpusConcatFilter(IterableCorpus):
    def __init__(self, pipeline, input_datatypes, **kwargs):
        self._master_raw_data = False
        self.input_datatypes = input_datatypes
        IterableCorpus.__init__(self, None, pipeline, **kwargs)

    def __len__(self):
        return sum((len(d) for d in self.input_datatypes), 0)

    def __iter__(self):
        return chain(*self.input_datatypes)

    def data_ready(self):
        return all(d.data_ready() for d in self.input_datatypes)

    def _set_raw_data(self, val):
        self._master_raw_data = val
        # Set on all the datasets
        for d in self.input_datatypes:
            d.raw_data = val

    def _get_raw_data(self):
        return self._master_raw_data

    raw_data = property(_get_raw_data, _set_raw_data)


class TarredCorpusConcatFilter(TarredCorpus):
    def __init__(self, pipeline, input_datatypes, **kwargs):
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

        for dataset_num, dataset in enumerate(self.input_datatypes):
            # This prefix is applied to every archive name in the corpus
            dataset_prefix = "corpus%02d_" % dataset_num

            to_skip = None
            if not started:
                if start_after is not None:
                    if start_after[0].startswith(dataset_prefix):
                        # The starting archive is somewhere in this dataset
                        start_archive = start_after[0][len(dataset_prefix):]
                        dataset_iter = dataset.archive_iter(start_after=(start_archive, start_after[1]))
                        start_after = None
                    else:
                        # The starting archive isn't in this dataset, so we can skip it
                        continue
                else:
                    # If we've still got more left to skip than are in this corpus, we can skip the whole thing
                    if skip - skipped > len(dataset):
                        skipped += len(dataset)
                        continue
                    else:
                        dataset_iter = dataset.archive_iter()

                if skip is not None:
                    to_skip = skip - skipped
            else:
                dataset_iter = dataset.archive_iter()

            for archive_name, doc_name, doc in islice(dataset_iter, to_skip, None):
                started = True
                yield u"%s%s" % (dataset_prefix, archive_name), doc_name, doc

    def list_archive_iter(self):
        for dataset_num, dataset in enumerate(self.input_datatypes):
            dataset_prefix = "corpus%02d_" % dataset_num
            for tar_name, filename in dataset.list_archive_iter():
                yield u"%s%s" % (dataset_prefix, tar_name), filename

    def data_ready(self):
        return all(d.data_ready() for d in self.input_datatypes)


def tarred_corpus_concat_filter_dp_type(dp_type):
    class TarredCorpusConcatFilterSubtype(TarredCorpusConcatFilter):
        data_point_type = dp_type
    return TarredCorpusConcatFilterSubtype


def corpus_concat_filter_dp_type(dp_type):
    class CorpusConcatFilterSubtype(CorpusConcatFilter):
        data_point_type = dp_type
    return CorpusConcatFilterSubtype


class DataPointTypeFromInputs(DynamicOutputDatatype):
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
        datatypes = module_info.get_input_datatype(self.input_name, always_list=True)
        # If the input datatype emulates another, it is that other that we will produce as output
        datatypes = [datatype.emulated_datatype or datatype for datatype in datatypes]
        # Find the common data point type to use for the output
        dp_type = _common_data_point_type([d.data_point_type for d in datatypes])
        # Check whether the inputs are all tarred corpora
        if all(issubclass(datatype, TarredCorpus) for datatype in datatypes):
            return tarred_corpus_with_data_point_type(dp_type)
        else:
            # If they're not all tarred corpora, just produce an iterable corpus
            return iterable_corpus_with_data_point_type(dp_type)


class ModuleInfo(BaseModuleInfo):
    module_type_name = "concat"
    module_readable_name = "Corpus concatenation"
    module_inputs = [("corpora", MultipleInputs(IterableCorpus))]
    module_outputs = [("corpus", DataPointTypeFromInputs())]
    module_executable = False

    def instantiate_output_datatype(self, output_name, output_datatype, **kwargs):
        datatypes = self.get_input("corpora", always_list=True)
        # Find the common datapoint type to use for the output corpus
        dp_type = _common_data_point_type([d.data_point_type for d in datatypes])

        if issubclass(output_datatype, TarredCorpus):
            filter_type = tarred_corpus_concat_filter_dp_type(dp_type)
        else:
            filter_type = corpus_concat_filter_dp_type(dp_type)

        return filter_type(self.pipeline, datatypes, module=self)
