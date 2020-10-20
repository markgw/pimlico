# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Textual corpus type where each word is accompanied by some annotations.

"""
from builtins import str
from collections import OrderedDict

from pimlico.core.modules.options import comma_separated_strings
from pimlico.datatypes import DynamicOutputDatatype, DatatypeLoadError
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType
from pimlico.utils.core import cached_property

SENTENCE_DIVIDER = "\n<SENT>\n"
NULL_ANNOTATION = "<NONE>"


def _encode_token(tok):
    """
    Replace any linebreaks and tabs
    """
    if tok is None:
        return NULL_ANNOTATION
    return tok.replace("\n", "<LINEBREAK>").replace("\t", "<TAB>")


def _decode_token(tok):
    if tok == NULL_ANNOTATION:
        return None
    return tok.replace("<LINEBREAK>", "\n").replace("<TAB>", "\t")


class WordAnnotationsDocumentType(TokenizedDocumentType):
    """
    List of sentences, each consisting of a list of word, each consisting of a
    tuple of the token and its annotations.

    The document type needs to know what fields will be provided, so that it's
    possible for a module to require a particular set of fields. The field list
    also tells the reader in which position to find each field.

    E.g. the field list "word,lemma,pos" will store values like "walks|walk|VB"
    for each token. You could also provide "word,pos,lemma" with "walks|VB|walk"
    and the reader would know where to find the fields it needs.

    When a WordAnnotationsDocumentType is used as an input type requirement, it
    will accept any input corpus that also has a WordAnnotationsDocumentType as
    its data-point type and includes at least all of the fields specified for
    the requirement.

    So, a requirement of
    ``GroupedCorpus(WordAnnotationsDocumentType(["word", "pos"]))`` will match
    a supplied type of ``GroupedCorpus(WordAnnotationsDocumentType(["word", "pos"]))``,
    or ``GroupedCorpus(WordAnnotationsDocumentType(["word", "pos", "lemma]))``,
    but not ``GroupedCorpus(WordAnnotationsDocumentType(["word", "lemma"]))``.

    Annotations are given as strings, not other types (like ints). If you want
    to store e.g. int or float annotations, you need to do the conversion
    separately, as the encoding and decoding assumes only strings are used.

    Annotations may, however, be ``None``. This, as well as any linebreaks and
    tabs in the strings, will be encoded/decoded by the writer/reader.

    """
    data_point_type_options = OrderedDict([
        ("fields", {
            "type": comma_separated_strings,
            "required": True,
            "help": "Names of the annotation fields. These include the word itself. Typically the first "
                    "field is therefore called 'word', but this is not required. However, there must be "
                    "a field called 'word', since this datatype overrides tokenized documents, so need "
                    "to be able to provide the original text. "
                    "When used as a module type requirement, the field list gives all the fields that "
                    "must (at least) be provided by the supplied type. "
                    "Specified as a comma-separated list. Required",
        }),
    ])
    data_point_type_supports_python2 = True

    def __init__(self, *args, **kwargs):
        self.fields = []
        self.field_pos = {}
        super(WordAnnotationsDocumentType, self).__init__(*args, **kwargs)
        self.fields = self.options["fields"]
        self.field_pos = dict([(field, pos) for (pos, field) in enumerate(self.fields)])

    def check_type(self, supplied_type):
        if not isinstance(supplied_type, WordAnnotationsDocumentType):
            return False
        # Make sure the supplied type has all of the required fields
        # It may have more, but must have at least these
        for req_field in self.fields:
            if req_field not in supplied_type.fields:
                return False
        return True

    def __repr__(self):
        return "{}({})".format(self.name, ", ".join(self.fields))

    class Document(object):
        keys = ["word_annotations"]

        @cached_property
        def text(self):
            return "\n".join(" ".join(word for word in sentence) for sentence in self.sentences)

        @cached_property
        def sentences(self):
            return self.get_field("word")

        def get_field(self, field):
            """
            Get the given field for every word in every sentence.

            Must be one of the fields available in this datatype.

            """
            field_pos = self.data_point_type.field_pos[field]
            return [[word[field_pos] for word in sentence] for sentence in self.internal_data["word_annotations"]]

        def raw_to_internal(self, raw_data):
            # Decode UTF8
            text = raw_data.decode("utf-8")
            # Split sentences: they're divided by a special sentence divider line
            sentences = text.split(SENTENCE_DIVIDER)
            # Split words: one line each
            # Each word has tab-separated annotations
            word_annotations = [
                [tuple([_decode_token(field) for field in word.split("\t")]) for word in sentence.splitlines()]
                for sentence in sentences
            ]
            return {"word_annotations": word_annotations}

        def internal_to_raw(self, internal_data):
            return SENTENCE_DIVIDER.join(
                "\n".join(
                    "\t".join(_encode_token(field) for field in word)
                    for word in sentence
                ) for sentence in internal_data["word_annotations"]
            ).encode("utf-8")


class AddAnnotationField(DynamicOutputDatatype):
    """
    Dynamic type constructor that can be used in place of a module's output type. When called
    (when the output type is needed), dynamically creates a new type that is a corpus with
    WordAnnotationsDocumentType with the same fields as the named input to the module,
    with the addition of one or more new ones.

    :param input_name: input to the module whose fields we extend
    :param add_fields: field or fields to add, string names
    """

    def __init__(self, input_name, add_fields):
        super(AddAnnotationField, self).__init__()
        # Make it easy to add just a single field, the most common case
        self.input_name = input_name

        if isinstance(add_fields, str):
            add_fields = [add_fields]
        self.add_fields = add_fields
        self.datatype_doc_info = ":class:WordAnnotationCorpus with %s" % ", ".join(add_fields)

    def get_datatype(self, module_info):
        from pimlico.core.modules.base import ModuleInfoLoadError
        from pimlico.datatypes import GroupedCorpus

        input_datatype = module_info.get_input_datatype(self.input_name)
        # Allow the special case where the input datatype is a tokenized corpus
        # Pretend it's an annotated corpus with no annotations, just words
        if not isinstance(input_datatype, GroupedCorpus):
            raise DatatypeLoadError("tried to add word annotations fields to input '{}', but that input is "
                                    "not a corpus type".format(self.input_name))
        elif isinstance(input_datatype.data_point_type, TokenizedDocumentType):
            # Special case where the input is tokenized documents: we can handle that, since it's
            # just like an annotated corpus with only the 'word' field
            base_fields = ["word"]
        elif not isinstance(input_datatype.data_point_type, WordAnnotationsDocumentType):
            raise DatatypeLoadError("input corpus '{}' has document type '{}'. Need TokenizedDocumentType or "
                                    "WordAnnotationsDocumentType to be able to extend the annotation fields"
                                    .format(self.input_name, input_datatype.data_point_type))
        else:
            base_fields = input_datatype.fields

        for field in self.add_fields:
            if field in base_fields:
                raise ModuleInfoLoadError("trying to add a field '{}' to data that already has a field with "
                                          "that name".format(field))
        return GroupedCorpus(WordAnnotationsDocumentType(base_fields + self.add_fields))

    def get_base_datatype(self):
        from pimlico.datatypes import GroupedCorpus
        return GroupedCorpus(WordAnnotationsDocumentType(["fields..."]))


AddAnnotationFields = AddAnnotationField


# Predefine some sets of annotations that can be used as input requirements
class DependencyParsedDocumentType(WordAnnotationsDocumentType):
    """
    WordAnnotationsDocumentType with fields word, pos, head, deprel for each token.

    Convenience wrapper for use as an input requirement where parsed text is needed.

    """
    def __init__(self, *args, **kwargs):
        kwargs["fields"] = ["word", "pos", "head", "deprel"]
        super().__init__(*args, **kwargs)
