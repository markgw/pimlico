from pimlico.cli.browser.formatter import DocumentBrowserFormatter
from pimlico.datatypes.tokenized import TokenizedDocumentType


class TokenizedDocumentFormatter(DocumentBrowserFormatter):
    DATATYPE = TokenizedDocumentType

    def __init__(self, corpus, raw_data=False):
        super(TokenizedDocumentFormatter, self).__init__(corpus)
        self.raw_data = raw_data

    def format_document(self, doc):
        if self.raw_data:
            # We're just showing the raw data, so don't try to do anything other than ensure it's a string
            doc = unicode(doc)
        else:
            doc = u"\n".join(u" ".join(words) for words in doc)
        return doc
