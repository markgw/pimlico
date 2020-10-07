# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from pimlico.old_datatypes.jsondoc import JsonDocumentCorpus, JsonDocumentType, JsonDocumentCorpusWriter
from pimlico.old_datatypes.tar import pass_up_invalid


class SentenceSpansDocumentType(JsonDocumentType):
    def process_document(self, doc):
        data = super(SentenceSpansDocumentType, self).process_document(doc)
        return [
            # Produce pairs of a tokenized sentence and a list of spans, each consisting of a start and end index
            (list(sentence_data["tokens"]), [(start, end) for (start, end) in sentence_data["spans"]])
            for sentence_data in data
        ]


class SentenceSpansCorpus(JsonDocumentCorpus):
    data_point_type = SentenceSpansDocumentType


class SentenceSpansCorpusWriter(JsonDocumentCorpusWriter):
    @pass_up_invalid
    def document_to_raw_data(self, doc):
        # Basically just makes sure the dicts have the right two keys
        return super(SentenceSpansCorpusWriter, self).document_to_raw_data([
            {
                "tokens": tokens,
                "spans": spans,
            } for (tokens, spans) in doc
        ])
