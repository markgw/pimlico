# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import cPickle as pickle
import os
import struct
from decimal import Decimal
from operator import itemgetter

from pimlico.old_datatypes.base import IterableCorpus, DatatypeLoadError, IterableCorpusWriter
from pimlico.old_datatypes.documents import RawDocumentType, DataPointType
from pimlico.old_datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid

__all__ = [
    "KeyValueListCorpus", "KeyValueListCorpusWriter", "KeyValueListDocumentType",
    "TermFeatureListCorpus", "TermFeatureListCorpusWriter", "TermFeatureListDocumentType",
    "IndexedTermFeatureListCorpus", "IndexedTermFeatureListCorpusWriter", "IndexedTermFeatureListDataPointType",
    "FeatureListScoreCorpus", "FeatureListScoreCorpusWriter", "FeatureListScoreDocumentType",
]


class KeyValueListDocumentType(RawDocumentType):
    def __init__(self, options, metadata):
        super(KeyValueListDocumentType, self).__init__(options, metadata)
        self.separator = self.metadata.get("separator", " ")
        self.fv_separator = self.metadata.get("fv_separator", "=")

    def process_document(self, doc):
        # Read a set of feature-value pairs from each line
        data_points = []
        for line in doc.splitlines():
            # Skip blank lines
            if line.strip():
                # Split up the various feature assignments
                fvs = line.strip().split(self.separator)
                # Now we've split on sep, unescape any instances that were escaped
                fvs = [unescape_sep(self.separator, "ITEMSEP", fv) for fv in fvs]
                # Split each one into a feature-value pair
                fvs = [itemgetter(0, 2)(fv.partition(self.fv_separator)) for fv in fvs]
                # Unescape the fv sep within feature names and feature values
                fvs = [
                    (unescape_sep(self.fv_separator, "FVSEP", fv[0]), unescape_sep(self.fv_separator, "FVSEP", fv[1]))
                    for fv in fvs
                ]
                data_points.append(fvs)
        return data_points


class KeyValueListCorpus(TarredCorpus):
    datatype_name = "key_value_lists"
    data_point_type = KeyValueListDocumentType


class KeyValueListCorpusWriter(TarredCorpusWriter):
    def __init__(self, base_dir, separator=" ", fv_separator="=", **kwargs):
        super(KeyValueListCorpusWriter, self).__init__(base_dir, **kwargs)
        self.fv_separator = fv_separator
        self.separator = separator
        # Put the separators in the metadata, so we know how to read the data in again
        self.metadata["separator"] = separator
        self.metadata["fv_separator"] = fv_separator
        self.write_metadata()

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        # Input should be a list of data points, where each is a list of feature-value pairs
        # One data point per line
        return "\n".join([
            # Fv pairs are separated by separator
            self.separator.join([
                # Make sure they don't include the separator
                escape_sep(
                    self.separator, "ITEMSEP",
                    # Feature and value are separated by fv_separator
                    "%s%s%s" % (
                        # Make sure they don't include the fv separator
                        escape_sep(self.fv_separator, "FVSEP", feature_name),
                        self.fv_separator,
                        escape_sep(self.fv_separator, "FVSEP", feature_value)
                    )
                ) for (feature_name, feature_value) in data_point
            ]) for data_point in doc
        ])


class TermFeatureListDocumentType(KeyValueListDocumentType):
    def process_document(self, doc):
        raw_data_points = super(TermFeatureListDocumentType, self).process_document(doc)
        data_points = []

        for data_point in raw_data_points:
            # Pull out the special "term" feature (usually at the beginning)
            try:
                term = (value for (feature, value) in data_point if feature == "term").next()
            except StopIteration:
                # No "term" feature found -- uh-oh! Catch as invalid doc
                raise ValueError("data point has no 'term' feature: %s" % data_point)
            # The rest of the features are feature counts
            features = dict((feature, int(value)) for (feature, value) in data_point if feature != "term")
            data_points.append((term, features))
        return data_points


class TermFeatureListCorpus(KeyValueListCorpus):
    """
    Special case of KeyValueListCorpus, where one special feature "term" is always present and the other
    feature types are counts of the occurrence of a particular feature with this term in each data point.

    """
    datatype_name = "term_feature_lists"
    data_point_type = TermFeatureListDocumentType


class TermFeatureListCorpusWriter(KeyValueListCorpusWriter):
    def __init__(self, base_dir, **kwargs):
        super(TermFeatureListCorpusWriter, self).__init__(base_dir, separator=" ", fv_separator="=", **kwargs)

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        # Input should be a list of data points, where each is a (term, feature count) pair
        #  and each feature count is a dictionary mapping feature names to counts
        data = [
            [("term", term)] + [(feature, str(count)) for (feature, count) in feature_counts.items()]
            for (term, feature_counts) in doc
        ]
        return super(TermFeatureListCorpusWriter, self).document_to_raw_data(data)


BYTE_FORMATS = {
    # (num bytes, signed)
    (1, True): "b",   # signed char
    (1, False): "B",  # unsigned char
    (2, True): "h",   # signed short
    (2, False): "H",  # unsigned short
    (4, True): "l",   # signed long
    (4, False): "L",  # unsigned long
    (8, True): "q",   # signed long long
    (8, False): "Q",  # unsigned long long
}

def get_struct(bytes, signed):
    # Put together the formatting string for converting ints to bytes
    if (bytes, signed) not in BYTE_FORMATS:
        raise ValueError("invalid specification for int format: signed=%s, bytes=%s. signed must be bool, "
                         "bytes in [1, 2, 4, 8]" % (signed, bytes))
    format_string = "<" + BYTE_FORMATS[(bytes, signed)]
    # Compile the format for faster encoding
    return struct.Struct(format_string)


class IndexedTermFeatureListDataPointType(DataPointType):
    pass


class IndexedTermFeatureListCorpus(IterableCorpus):
    """
    Term-feature instances, indexed by a dictionary, so that all that's stored is the indices of the terms
    and features and the feature counts for each instance. This is iterable, but, unlike TermFeatureListCorpus,
    doesn't iterate over documents. Now that we've filtered extracted features down to a smaller vocab, we
    put everything in one big file, with one data point per line.

    Since we're now storing indices, we can use a compact format that's fast to read from disk, making iterating
    over the dataset faster than if we had to read strings, look them up in the vocab, etc.

    By default, the ints are stored as C longs, which use 4 bytes. If you know you don't need ints this
    big, you can choose 1 or 2 bytes, or even 8 (long long). By default, the ints are unsigned, but they
    may be signed.

    """
    data_point_type = IndexedTermFeatureListDataPointType

    def __init__(self, *args, **kwargs):
        super(IndexedTermFeatureListCorpus, self).__init__(*args, **kwargs)
        self._term_dictionary = None
        self._feature_dictionary = None

    @property
    def term_dictionary(self):
        if self._term_dictionary is None:
            # Read in the dictionary from a file
            with open(os.path.join(self.data_dir, "term_dictionary"), "r") as f:
                self._term_dictionary = pickle.load(f)
        return self._term_dictionary

    @property
    def feature_dictionary(self):
        if self._feature_dictionary is None:
            # Read in the dictionary from a file
            with open(os.path.join(self.data_dir, "feature_dictionary"), "r") as f:
                self._feature_dictionary = pickle.load(f)
        return self._feature_dictionary

    def __iter__(self):
        # Check how many bytes to use per int
        bytes = self.metadata.get("bytes", 4)
        signed = self.metadata.get("signed", False)
        # Prepare a struct for reading one int at a time
        int_unpacker = get_struct(bytes, signed)
        # Prepare another struct for reading the number of feature counts in a data point
        length_unpacker = get_struct(2, False)

        with open(os.path.join(self.data_dir, "data"), "r") as data_file:
            try:
                while True:
                    # Read data for a single int - the term
                    term = _read_binary_int(data_file, int_unpacker)
                    # Next digit tells us the number of feature counts in this data point
                    num_features = _read_binary_int(data_file, length_unpacker)
                    # Now read two ints for every feature: the feature id and the count
                    feature_counts = dict(
                        (_read_binary_int(data_file, int_unpacker), _read_binary_int(data_file, int_unpacker))
                        for i in range(num_features)
                    )
                    yield term, feature_counts
            except StopIteration:
                # Reached end of file
                pass


class IndexedTermFeatureListCorpusWriter(IterableCorpusWriter):
    """
    index_input=True means that the input terms and feature names are already mapped to dictionary indices, so
    are assumed to be ints. Otherwise, inputs will be looked up in the appropriate dictionary to get an index.

    """
    def __init__(self, base_dir, term_dictionary, feature_dictionary, bytes=4, signed=False, index_input=False,
                 **kwargs):
        super(IndexedTermFeatureListCorpusWriter, self).__init__(base_dir, **kwargs)
        self.metadata["bytes"] = bytes
        self.metadata["signed"] = signed
        self.write_metadata()

        self.feature_dictionary = feature_dictionary
        self.term_dictionary = term_dictionary
        # Write the dictionaries out to disk straight away
        self.write_dictionaries()

        self.int_packer = get_struct(self.metadata["bytes"], self.metadata["signed"])
        self.length_packer = get_struct(2, False)
        self.index_input = index_input

        self._added_data_points = 0

    def write_dictionaries(self):
        with open(os.path.join(self.data_dir, "term_dictionary"), "w") as f:
            pickle.dump(self.term_dictionary, f, -1)
        with open(os.path.join(self.data_dir, "feature_dictionary"), "w") as f:
            pickle.dump(self.feature_dictionary, f, -1)

    def __enter__(self):
        self.data_file = open(os.path.join(self.data_dir, "data"), "w")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.data_file.close()
        # Set the length to be the number of data points written
        self.metadata["length"] = self._added_data_points
        super(IndexedTermFeatureListCorpusWriter, self).__exit__(exc_type, exc_val, exc_tb)

    def add_data_points(self, iterable):
        for term, feature_counts in iterable:
            feature_counts = feature_counts.items()
            if not self.index_input:
                # Look up indices in the dictionaries
                if term not in self.term_dictionary.token2id:
                    # Skip unknown terms
                    continue
                term = self.term_dictionary.token2id[term]
                # Look up all feature name indices, skipping unknown features
                feature_counts = [(self.feature_dictionary.token2id[f], cnt) for (f, cnt) in feature_counts
                                  if f in self.feature_dictionary.token2id]
            # Filter out zero counts
            feature_counts = [(f, c) for (f, c) in feature_counts if c > 0]
            if len(feature_counts) == 0:
                # If there aren't any features left after filtering on dictionary and counts, skip whole data point
                continue

            # Now we've converted to indices, write the data out
            # First write the term index
            _write_binary_int(self.data_file, self.int_packer, term)
            # Next the number of feature counts so we know how much to read when reading in
            _write_binary_int(self.data_file, self.length_packer, len(feature_counts))
            # Now all the features and their counts
            for f, c in feature_counts:
                _write_binary_int(self.data_file, self.int_packer, f)
                _write_binary_int(self.data_file, self.int_packer, c)

            # Keep a record of how much data we wrote so we can make the corpus length available to future modules
            self._added_data_points += 1


class FeatureListScoreDocumentType(RawDocumentType):
    """
    Document type that stores a list of features, each associated with a floating-point score. The feature lists
    are simply lists of indices to a feature set for the whole corpus that includes all feature types and which
    is stored along with the dataset. These may be binary features (present or absent for each data point), or
    may have a weight associated with them. If they are binary, the returned data will have a weight of 1 associated
    with each.

    A corpus of this type can be used to train, for example, a regression.

    If scores and weights are passed in as Decimal objects, they will be stored as strings. If they are floats,
    they will be converted to Decimals via their string representation (avoiding some of the oddness of converting
    between binary and decimal representations). To avoid loss of precision, pass in all scores and weights as
    Decimal objects.

    """
    formatters = [("features", "pimlico.datatypes.formatters.features.FeatureListScoreFormatter")]

    def __init__(self, options, metadata):
        super(FeatureListScoreDocumentType, self).__init__(options, metadata)
        self.features = self.metadata.get("features", [])
        self.separator = self.metadata.get("separator", ":")

    def process_document(self, doc):
        # Read a set of feature-value pairs from each line
        data_points = []
        for line in doc.splitlines():
            # Skip blank lines
            if line.strip():
                # The score is at the start of the line, before the list of features
                score, __, feature_str = line.partition(self.separator)
                # The score should always be a Decimal
                score = Decimal(score)
                weighted_features = []
                for feature in feature_str.strip().split(","):
                    if "=" in feature:
                        # This feature has a weight/count
                        feature, __, weight = feature.partition("=")
                        weight = Decimal(weight)
                    else:
                        # No weight given: default to 1
                        weight = Decimal(1)
                    # Features should be represented as ints: indices in feature list
                    weighted_features.append((int(feature), weight))
                data_points.append((score, weighted_features))
        return data_points


class FeatureListScoreCorpus(TarredCorpus):
    datatype_name = "scored_weight_feature_lists"
    data_point_type = FeatureListScoreDocumentType


class FeatureListScoreCorpusWriter(TarredCorpusWriter):
    """
    Input should be a list of data points. Each is a (score, feature list) pair, where score is a
    Decimal, or other numeric type. Feature list is a list of (feature name, weight) pairs, or just
    feature names. If weights are not given, they will default to 1 when read in (but no weight is
    stored).

    If index_input=True, it is assumed that feature IDs will be given instead of feature names.
    Otherwise, the feature names will be looked up in the feature list. Any features not found in the
    feature type list will simply be skipped.

    """
    def __init__(self, base_dir, features, separator=":", index_input=False, **kwargs):
        super(FeatureListScoreCorpusWriter, self).__init__(base_dir, **kwargs)
        self.index_input = index_input
        self.separator = separator
        self.features = features
        # Put the separators in the metadata, so we know how to read the data in again
        self.metadata["separator"] = separator
        self.metadata["features"] = features
        self.write_metadata()

    def _num_to_dec(self, num):
        if isinstance(num, Decimal):
            return num
        elif isinstance(num, float):
            # Convert floats to strings first, which deals with some binary weirdness, then to Decimals
            return Decimal(str(num))
        else:
            # Try using Decimal's own init to convert to a Decimal
            return Decimal(num)

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        if self.index_input:
            # Expect indices to be given, so don't look up feature names
            _feature_to_id = lambda x: x
            _valid_feature = lambda x: True
        else:
            feature_dict = dict((feature, id) for (id, feature) in enumerate(self.features))
            # Shouldn't got a feature that isn't in the list of feature types list, as we're skipping them
            _feature_to_id = lambda x: feature_dict[x]
            _valid_feature = lambda x: x[0] in feature_dict if type(x) is tuple else x in feature_dict

        # One data point per line
        return "\n".join(
            "%s: %s" % (
                self._num_to_dec(score),
                ",".join(
                    "%d=%s" % (_feature_to_id(feature[0]), self._num_to_dec(feature[1])) if type(feature) is tuple
                    else "%d" % _feature_to_id(feature)
                    for feature in features if _valid_feature(feature)
                )
            ) for (score, features) in doc
        )


def _read_binary_int(f, unpacker):
    # Read the right number of bytes from the file
    string = f.read(unpacker.size)
    if string == "":
        raise StopIteration
    try:
        # Try decoding this as a single int
        integer = unpacker.unpack(string)[0]
    except struct.error, e:
        raise DatatypeLoadError("could not unpack integer data in file: corrupt data? %s" % e)
    return integer


def _write_binary_int(f, packer, x):
    string = packer.pack(x)
    f.write(string)


def escape_sep(sep, sep_type, text):
    return text.replace(sep, "~~%s~~" % sep_type)


def unescape_sep(sep, sep_type, text):
    return text.replace("~~%s~~" % sep_type, sep)
