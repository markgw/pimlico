from pimlico.cli.browser.formatter import DocumentBrowserFormatter
from pimlico.old_datatypes.tokenized import TokenizedDocumentType, CharacterTokenizedDocumentType, \
    SegmentedLinesDocumentType


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


class CharacterTokenizedDocumentFormatter(DocumentBrowserFormatter):
    DATATYPE = CharacterTokenizedDocumentType

    def __init__(self, corpus, raw_data=False):
        super(CharacterTokenizedDocumentFormatter, self).__init__(corpus)
        self.raw_data = raw_data

    def format_document(self, doc):
        if self.raw_data:
            # We're just showing the raw data, so don't try to do anything other than ensure it's a string
            doc = unicode(doc)
        else:
            doc = u"\n".join(u"".join(chars) for chars in doc)
        return doc


class SegmentedLinesFormatter(DocumentBrowserFormatter):
    DATATYPE = SegmentedLinesDocumentType

    def format_document(self, doc):
        return u"\n".join(" ".join(line) for line in doc)
