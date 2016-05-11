# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Datatypes for coreference resolution output. Based on OpenNLP's coref output, so includes all the information
provided by that.
This is a slight different set of information to CoreNLP. Currently, there's no way to convert between the
two datatypes, but in future it will be easy to provide an adapter that carries across the information common
to the two (which for most purposes will be sufficient).

"""

from pimlico.datatypes.jsondoc import JsonDocumentCorpus, JsonDocumentCorpusWriter
from pimlico.datatypes.tar import pass_up_invalid
from pimlico.utils.strings import truncate


class CorefCorpus(JsonDocumentCorpus):
    datatype_name = "opennlp_coref"

    def process_document(self, data):
        data = super(CorefCorpus, self).process_document(data)
        return list(sorted([Entity.from_json(entity) for entity in data], key=lambda e: e.id))


class CorefCorpusWriter(JsonDocumentCorpusWriter):
    @pass_up_invalid
    def document_to_raw_data(self, doc):
        return super(CorefCorpusWriter, self).document_to_raw_data([
            entity.to_json_dict() for entity in doc
        ])


class Entity(object):
    def __init__(self, id, mentions, category=None, gender=None, gender_prob=None, number=None, number_prob=None):
        self.category = category
        self.gender = gender
        self.gender_prob = gender_prob
        self.number = number
        self.number_prob = number_prob
        self.id = id
        self.mentions = mentions

    def to_json_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "gender": self.gender,
            "genderProb": self.gender_prob,
            "number": self.number,
            "numberProb": self.number_prob,
            "mentions": [m.to_json_dict() for m in self.mentions],
        }

    @staticmethod
    def from_json(json):
        return Entity(
            json["id"],
            [Mention.from_json(m) for m in json["mentions"]],
            json.get("category", None), json.get("gender", None), json.get("genderProb", None),
            json.get("number", None), json.get("numberProb", None)
        )

    @staticmethod
    def from_java_object(obj):
        return Entity(
            obj.getId(),
            [Mention.from_java_object(m) for m in obj.getMentions()],
            category=obj.getCategory(), gender=obj.getGender().toString(), gender_prob=obj.getGenderProbability(),
            number=obj.getNumber().toString(), number_prob=obj.getNumberProbability()
        )

    def __unicode__(self):
        return u"Entity-%s(%s)" % (self.id, "/".join(truncate(unicode(m), 15).strip() for m in self.mentions))

    def __repr__(self):
        return unicode(self).encode("ascii", "ignore")


class Mention(object):
    def __init__(self, sentence_num, start_index, end_index, text,
                 gender=None, gender_prob=None, number=None, number_prob=None,
                 head_start_index=None, head_end_index=None, name_type=None):
        self.sentence_num = sentence_num
        self.start_index = start_index
        self.end_index = end_index
        self.text = text
        self.gender = gender
        self.gender_prob = gender_prob
        self.number = number
        self.number_prob = number_prob
        self.head_start_index = head_start_index
        self.head_end_index = head_end_index
        self.name_type = name_type

    @staticmethod
    def from_json(json):
        return Mention(
            json["sentNum"], json["startIndex"], json["endIndex"], json["text"],
            json.get("gender", None), json.get("genderProb", None),
            json.get("number", None), json.get("numberProb", None),
            json.get("headStartIndex", None), json.get("headEndIndex", None), json.get("nameType", None),
        )

    def to_json_dict(self):
        data = {
            "sentNum": self.sentence_num, "startIndex": self.start_index, "endIndex": self.end_index,
            "text": self.text,
        }
        if self.gender is not None:
            data["gender"] = self.gender
        if self.gender_prob is not None:
            data["genderProb"] = self.gender_prob
        if self.number is not None:
            data["number"] = self.number
        if self.number_prob is not None:
            data["numberProb"] = self.number_prob
        if self.head_start_index is not None:
            data["headStartIndex"] = self.head_start_index
        if self.head_end_index is not None:
            data["headEndIndex"] = self.head_end_index
        if self.name_type is not None:
            data["nameType"] = self.name_type
        return data

    @staticmethod
    def from_java_object(obj):
        return Mention(
            obj.getSentenceNumber(), obj.getIndexSpan().getStart(), obj.getIndexSpan().getEnd(),
            obj.toText(),
            obj.getGender().toString(), obj.getGenderProb(), obj.getNumber().toString(), obj.getNumberProb(),
            obj.getHeadSpan().getStart(), obj.getHeadSpan().getEnd(), obj.getNameType()
        )

    def __unicode__(self):
        return unicode(self.text)
