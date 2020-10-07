# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Datatypes for coreference resolution output. Based on OpenNLP's coref output, so includes all the information
provided by that.
This is a slight different set of information to CoreNLP. Currently, there's no way to convert between the
two datatypes, but in future it will be easy to provide an adapter that carries across the information common
to the two (which for most purposes will be sufficient).

"""

from pimlico.old_datatypes.jsondoc import JsonDocumentCorpus, JsonDocumentCorpusWriter, JsonDocumentType
from pimlico.old_datatypes.tar import pass_up_invalid
from pimlico.utils.linguistic import strip_punctuation, ENGLISH_PRONOUNS
from pimlico.utils.strings import truncate


class CorefDocumentType(JsonDocumentType):
    def process_document(self, doc):
        data = super(CorefDocumentType, self).process_document(doc)
        return list(sorted([Entity.from_json(entity) for entity in data], key=lambda e: e.id))


class CorefCorpus(JsonDocumentCorpus):
    datatype_name = "opennlp_coref"
    data_point_type = CorefDocumentType


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

    def get_head_word(self, pronouns=ENGLISH_PRONOUNS):
        """
        Retrieve a head word from the entity's mentions if possible. Returns None if no suitable head
        word can be found: e.g., if all mentions are pronouns.

        Pronouns are filtered out using :data:pimlico.utils.linguistic.ENGLISH_PRONOUNS by default. You can
        override this with the `pronouns` kwargs. If `pronouns=None`, no filtering is done.

        """
        entity_head_words = set()
        # Gather a head word, if possible, from each mention
        for mention in self.mentions:
            mention_head = mention.text[
                           mention.head_start_index-mention.start_index:mention.head_end_index-mention.start_index
                           ].lower()
            # Process the head phrase a bit
            # Remove punctuation
            mention_head = strip_punctuation(mention_head)
            # Get rid of words that won't help us: stopwords and pronouns
            head_words = mention_head.split()
            if pronouns is not None:
                head_words = [w for w in head_words if w not in pronouns]
            # Don't use any 1-letter words
            head_words = [w for w in head_words if len(w) > 1]
            # If there are no words left, we can't get a headword from this mention
            # If there are multiple (a minority of cases), use the rightmost, which usually is the headword
            if head_words:
                entity_head_words.add(head_words[-1])
        # If we've ended up with multiple possible head words (minority, but not uncommon), we've no way to choose
        # We could just pick one randomly
        # Take the lexicographic first, just to be consistent
        if len(entity_head_words):
            return list(sorted(entity_head_words))[0]
        else:
            return None

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
        return u"Entity-%s(%s)" % (self.id,
                                   truncate(u"/".join(truncate(unicode(m), 30).strip() for m in self.mentions), 30))

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
