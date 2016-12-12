# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Datatypes for coreference resolution output. Based on Stanford CoreNLP's coref output, so includes all the information
provided by that.

"""
import json

from pimlico.datatypes.jsondoc import JsonDocumentType, JsonDocumentCorpus
from pimlico.datatypes.tar import TarredCorpusWriter, pass_up_invalid


class CorefDocumentType(JsonDocumentType):
    def process_document(self, doc):
        data = super(CorefDocumentType, self).process_document(doc)
        return [Entity(eid, [Mention.from_json(m) for m in mentions]) for (eid, mentions) in data.items()]


class CorefCorpus(JsonDocumentCorpus):
    datatype_name = "corenlp_coref"
    data_point_type = CorefDocumentType


class CorefCorpusWriter(TarredCorpusWriter):
    @pass_up_invalid
    def document_to_raw_data(self, doc):
        return json.dumps(dict(
            (entity.id, [m.to_json_dict() for m in entity.mentions]) for entity in doc
        ))


class Entity(object):
    def __init__(self, id, mentions):
        self.id = id
        self.mentions = mentions


class Mention(object):
    def __init__(self, id, sentence_num, start_index, end_index, text, type,
                 position=None, animacy=None, is_representative_mention=None, number=None, gender=None):
        self.id = id
        self.sentence_num = sentence_num
        self.start_index = start_index
        self.end_index = end_index
        self.text = text
        self.type = type
        self.position = position
        self.animacy = animacy
        self.is_representative_mention = is_representative_mention
        self.number = number
        self.gender = gender

    @staticmethod
    def from_json(json):
        return Mention(
            json["id"], json["sentNum"], json["startIndex"], json["endIndex"], json["text"], json["type"],
            position=json.get("position", None), animacy=json.get("animacy", None),
            is_representative_mention=json.get("isRepresentativeMention", None),
            number=json.get("number", None), gender=json.get("gender", None)
        )

    def to_json_dict(self):
        data = {
            "id": self.id, "sentNum": self.sentence_num, "startIndex": self.start_index, "endIndex": self.end_index,
            "text": self.text, "type": self.type
        }
        if self.position is not None:
            data["position"] = self.position
        if self.animacy is not None:
            data["animacy"] = self.animacy
        if self.is_representative_mention is not None:
            data["isRepresentativeMention"] = self.is_representative_mention
        if self.number is not None:
            data["number"] = self.number
        if self.gender is not None:
            data["gender"] = self.gender
        return data
