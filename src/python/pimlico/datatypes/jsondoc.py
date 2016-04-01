import json
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid


class JsonDocumentCorpus(TarredCorpus):
    """
    Very simple document corpus in which each document is a JSON object.

    """

    def process_document(self, data):
        data = json.loads(data)
        return super(JsonDocumentCorpus, self).process_document(data)


class JsonDocumentCorpusWriter(TarredCorpusWriter):
    """
    If readable=True, JSON text output will be nicely formatted so that it's human-readable.
    Otherwise, it will be formatted to take up less space.
    """
    def __init__(self, base_dir, readable=False, **kwargs):
        super(JsonDocumentCorpusWriter, self).__init__(base_dir, **kwargs)
        self.readable = readable

    @pass_up_invalid
    def add_document(self, archive_name, doc_name, data):
        # Data should be a JSON object or other object serializable by the json package
        if self.readable:
            data = json.dumps(data, indent=4)
        else:
            # More compact representation, not very readable
            data = json.dumps(data, indent=None, separators=(",", ":"))
        super(JsonDocumentCorpusWriter, self).add_document(archive_name, doc_name, data)
