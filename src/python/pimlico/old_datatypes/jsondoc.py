# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import json

from pimlico.old_datatypes.documents import RawDocumentType
from pimlico.old_datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid


__all__ = ["JsonDocumentCorpus", "JsonDocumentCorpusWriter"]


class JsonDocumentType(RawDocumentType):
    def process_document(self, doc):
        return json.loads(doc)


class JsonDocumentCorpus(TarredCorpus):
    """
    Very simple document corpus in which each document is a JSON object.

    """
    datatype_name = "json"
    data_point_type = JsonDocumentType


class JsonDocumentCorpusWriter(TarredCorpusWriter):
    """
    If readable=True, JSON text output will be nicely formatted so that it's human-readable.
    Otherwise, it will be formatted to take up less space.
    """
    def __init__(self, base_dir, readable=False, **kwargs):
        super(JsonDocumentCorpusWriter, self).__init__(base_dir, **kwargs)
        self.readable = readable

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        # Data should be a JSON object or other object serializable by the json package
        if self.readable:
            return json.dumps(doc, indent=4)
        else:
            # More compact representation, not very readable
            return json.dumps(doc, indent=None, separators=(",", ":"))
