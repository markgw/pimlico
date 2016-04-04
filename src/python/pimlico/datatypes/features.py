from operator import itemgetter

from pimlico.core.modules.map import skip_invalid, invalid_doc_on_error
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid


class KeyValueListCorpus(TarredCorpus):
    def __init__(self, base_dir, pipeline):
        super(KeyValueListCorpus, self).__init__(base_dir, pipeline)
        self.separator = self.metadata.get("separator", " ")
        self.fv_separator = self.metadata.get("fv_separator", "=")

    @skip_invalid
    def process_document(self, data):
        # Read a set of feature-value pairs from each line
        data_points = []
        for line in data.splitlines():
            # Skip blank lines
            if line.strip():
                # Split up the various feature assignments
                fvs = line.strip().split(self.separator)
                # Now we've split on sep, unescape any instances that were escaped
                fvs = [unescape_sep(self.separator, "ITEMSEP", fv) for fv in fvs]
                # Split each one into a feature-value pair
                fvs = [itemgetter(0, 2)(fv.split(self.fv_separator)) for fv in fvs]
                # Unescape the fv sep within feature names and feature values
                fvs = [
                    (unescape_sep(self.fv_separator, "FVSEP", fv[0]), unescape_sep(self.fv_separator, "FVSEP", fv[1]))
                    for fv in fvs
                ]
                data_points.append(fvs)
        return data_points


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


class TermFeatureListCorpus(KeyValueListCorpus):
    """
    Special case of KeyValueListCorpus, where one special feature "term" is always present and the other
    feature types are counts of the occurrence of a particular feature with this term in each data point.

    """
    def __init__(self, base_dir, pipeline):
        super(TermFeatureListCorpus, self).__init__(base_dir, pipeline)

    @skip_invalid
    @invalid_doc_on_error
    def process_document(self, data):
        data = super(TermFeatureListCorpus, self).process_document(data)

        data_points = []
        for data_point in data:
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


def escape_sep(sep, sep_type, text):
    return text.replace(sep, "~~%s~~" % sep_type)


def unescape_sep(sep, sep_type, text):
    return text.replace("~~%s~~" % sep_type, sep)
