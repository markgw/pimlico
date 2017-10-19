# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.datatypes.jsondoc import JsonDocumentCorpus, JsonDocumentType, JsonDocumentCorpusWriter
from pimlico.datatypes.tar import pass_up_invalid


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
