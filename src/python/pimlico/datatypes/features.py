from pimlico.datatypes import NamedFileCollection
from pimlico.datatypes.base import DatatypeWriteError
from pimlico.utils.core import cached_property


class ScoredRealFeatureSets(NamedFileCollection):
    """
    Sets of features, where each feature has an associated real number value,
    and each set (i.e. data point) has a score.

    This is suitable as training data for a multidimensional regression.

    Stores a dictionary of feature types and uses integer IDs to refer to them
    in the data storage.

    .. todo::

       Add unit test for ScoredReadFeatureSets

    """
    datatype_name = "scored_real_feature_sets"

    def __init__(self, *args, **kwargs):
        super(ScoredRealFeatureSets, self).__init__(["feature_types.list", "data.csv"], *args, **kwargs)

    def browse_file(self, reader, filename):
        if filename == "data.csv":
            # Show feature names instead of IDs
            feature_names = reader.feature_types
            data = reader.read_file(filename)
            lines = [line.split() for line in data.splitlines()]
            return u"\n".join(u"{}: {}".format(row[0], u", ".join(u"{} ({:.2f})".format(feature_names[int(item.partition(":")[0])], float(item.partition(":")[2])) for item in row[1:])) for row in lines).encode("utf8")
        else:
            super(ScoredRealFeatureSets, self).browse_file(reader, filename)

    class Reader:
        def __iter__(self):
            for features, score in self.iter_ids():
                # Translate feature IDs into names
                yield dict((self.feature_types[f], v) for (f, v) in features.iteritems()), score

        def read_samples(self):
            """
            Read all samples in from the data file.

            Note that `__iter__()` iterates over the file without loading everything
            into memory, which may be preferable if dealing with big datasets.

            """
            return list(self)

        def iter_ids(self):
            """
            Iterate over the raw ID data from the data file, without translating feature
            type IDs into feature names.

            """
            with open(self.get_absolute_path("data.csv"), "r") as f:
                for line in f:
                    line.rstrip("\n")
                    values = line.split()
                    # The first value is the score
                    score = float(values[0])
                    # The rest are feature id -> value mappings
                    feature_id_vals = [val.split(":") for val in values[1:]]
                    features = dict((int(f), float(v)) for (f, v) in feature_id_vals)
                    yield features, score

        @cached_property
        def feature_types(self):
            data = self.read_file("feature_types.list")
            return data.decode("utf8").splitlines()

        @cached_property
        def num_samples(self):
            # Count the lines in the data file
            with open(self.get_absolute_path("data.csv"), "r") as f:
                return sum(1 for __ in f)

        def __len__(self):
            return self.num_samples

    class Writer:
        def set_feature_types(self, feature_types):
            """
            Explicitly set the list of feature types that will be written out.
            All feature types given will be included, plus possibly others that are
            used in the written samples, which will be added to the set.

            This can be useful if you want your feature vocabulary to include
            the whole of a given set, even if some feature types are never
            used in the data. It can also be useful to ensure particular IDs
            are used for particular feature types, if you care about that.

            """
            if len(self._used_feature_types) > 0:
                # The feature set has already started being constructed
                raise DatatypeWriteError("tried to set feature type list explicitly after it's already started "
                                         "being constructed implicitly (or has previously been set explicitly)")
            self._used_feature_types = list(feature_types)

        def write_samples(self, samples):
            """
            Writes a list of samples, each given as a (features, score) pair.
            See `write_sample()`

            """
            for (fs, score) in samples:
                self.write_sample(fs, score)

        def write_sample(self, features, score):
            """
            Write out a single sample to the end of the data file.
            Features should be given by name in a dictionary mapping the feature type
            to its value.

            :param features: dict(feature name -> feature value)
            :param score: score associated with this data point
            """
            # Map feature names to IDs, adding new feature types as necessary
            self._used_feature_types.extend(f for f in features.keys() if f not in self._used_feature_types)
            features_by_id = dict(
                (self._used_feature_types.index(f), val) for (f, val) in features.iteritems()
            )
            # Write out a line containing the score and each of the feature id -> value mappings
            self.data_file.write("{:f} {}\n".format(
                score,
                " ".join(u"{:d}:{:f}".format(f, v) for (f, v) in features_by_id.iteritems())
            ))

        def __enter__(self):
            obj = super(ScoredRealFeatureSets.Writer, self).__enter__()
            # Open the data file for writing: we'll write one data point per line
            self.data_file = open(self.get_absolute_path("data.csv"), "w")
            # Keep track of used feature types to output the dictionary at the end
            self._used_feature_types = []
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.data_file.close()
            self.task_complete("write_data.csv")
            # Write out the feature type dictionary
            self.write_file("feature_types.list", u"\n".join(self._used_feature_types).encode("utf8"))
            super(ScoredRealFeatureSets.Writer, self).__exit__(exc_type, exc_val, exc_tb)
