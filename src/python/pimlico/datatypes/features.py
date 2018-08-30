from pimlico.datatypes import IterableCorpus, PimlicoDatatype
from pimlico.datatypes.corpora import DataPointType


class ScoredRealFeatureSetType(DataPointType):
    class Document:
        # TODO
        pass


class ScoredRealFeatureSets(IterableCorpus):
    """
    Sets of features, where each feature has an associated real number value,
    and each set (i.e. data point) has a score.

    This is suitable as training data for a multidimensional regression.

    """
    datatype_name = "scored_real_feature_sets"
    data_point_type = ScoredRealFeatureSetType

    class Reader:
        # TODO Need some custom stuff on the reader to read from a single file
        pass

    class Writer:
        # TODO Write one data point per line
        pass
