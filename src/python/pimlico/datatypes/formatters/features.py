from pimlico.cli.browser.formatter import DocumentBrowserFormatter
from pimlico.datatypes import FeatureListScoreDocumentType


class FeatureListScoreFormatter(DocumentBrowserFormatter):
    DATATYPE = FeatureListScoreDocumentType

    def __init__(self, corpus):
        super(FeatureListScoreFormatter, self).__init__(corpus)
        self.feature_list = corpus.data_point_type_instance.features

    def format_document(self, doc):
        return u"\n".join(
            u"%s: %s" % (
                score,
                u", ".join(
                    self.feature_list[f] if weight == 1 else u"%s (%s)" % (self.feature_list[f], weight)
                    for (f, weight) in features
                )
            ) for (score, features) in doc
        )