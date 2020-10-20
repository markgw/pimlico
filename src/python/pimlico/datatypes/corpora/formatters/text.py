from pimlico.datatypes.corpora.data_points import TextDocumentType

from pimlico.cli.browser.tools.formatter import DocumentBrowserFormatter


class TextDocumentFormatter(DocumentBrowserFormatter):
    """
    Formatter for text document types for use in the corpus browser.

    Simply displays the unicode text that's stored for the document.

    """
    DATATYPE = TextDocumentType()

    def format_document(self, doc):
        return doc.text
