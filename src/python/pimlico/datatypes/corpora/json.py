# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import absolute_import
from builtins import object

import json

from pimlico.cli.browser.tools.formatter import DocumentBrowserFormatter
from pimlico.datatypes.corpora.data_points import RawDocumentType


__all__ = ["JsonDocumentType"]


class JsonDocumentType(RawDocumentType):
    """
    Very simple document corpus in which each document is a JSON object.

    """
    formatters = [("json", "pimlico.datatypes.corpora.json.JsonFormatter")]
    data_point_type_supports_python2 = True

    class Document(object):
        keys = ["data"]

        def raw_to_internal(self, raw_data):
            return {"data": json.loads(raw_data.decode("utf-8"))}

        def internal_to_raw(self, internal_data):
            return json.dumps(internal_data["data"]).encode("utf-8")


class JsonFormatter(DocumentBrowserFormatter):
    DATATYPE = JsonDocumentType()

    def format_document(self, doc):
        return json.dumps(doc.data, indent=4)
