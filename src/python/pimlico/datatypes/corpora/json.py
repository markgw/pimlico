# This file is part of Pimlico
# Copyright (C) 2018 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
from __future__ import absolute_import

import json

from pimlico.cli.browser.tools.formatter import DocumentBrowserFormatter
from pimlico.datatypes.corpora.data_points import RawDocumentType


__all__ = ["JsonDocumentType"]


class JsonDocumentType(RawDocumentType):
    """
    Very simple document corpus in which each document is a JSON object.

    """
    formatters = [("json", "pimlico.datatypes.corpora.json.JsonFormatter")]

    class Document:
        keys = ["data"]

        def raw_to_internal(self, raw_data):
            return {"data": json.loads(raw_data)}

        def internal_to_raw(self, internal_data):
            return json.dumps(internal_data["data"])


class JsonFormatter(DocumentBrowserFormatter):
    DATATYPE = JsonDocumentType()

    def format_document(self, doc):
        return json.dumps(doc.data, indent=4)