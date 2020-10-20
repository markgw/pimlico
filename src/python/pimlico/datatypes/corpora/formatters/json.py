import json

from pimlico.datatypes.corpora.json import JsonDocumentType

from pimlico.cli.browser.tools.formatter import DocumentBrowserFormatter


class JsonFormatter(DocumentBrowserFormatter):
    DATATYPE = JsonDocumentType()

    def format_document(self, doc):
        return json.dumps(doc.data, indent=4)
