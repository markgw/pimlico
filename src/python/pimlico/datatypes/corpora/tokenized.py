# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
from pimlico.datatypes.corpora.data_points import TextDocumentType

__all__ = ["TokenizedDocumentType", "SegmentedLinesDocumentType", "CharacterTokenizedDocumentType"]


class TokenizedDocumentType(TextDocumentType):
    """
    Specialized data point type for documents that have had tokenization applied.
    It does very little processing - the main reason for its existence is to allow
    modules to require that a corpus has been tokenized before it's given as input.

    Each document is a list of sentences. Each sentence is a list of words.

    """
    # TODO Update formatter and put back here
    #formatters = [("tokenized_doc", "pimlico.datatypes.formatters.tokenized.TokenizedDocumentFormatter")]

    class Document:
        @property
        def sentences(self):
            return self.internal_data["sentences"]

        def raw_to_internal(self, raw_data):
            return {"sentences": [sentence.split(u" ") for sentence in raw_data.split(u"\n")]}

        def internal_to_raw(self, internal_data):
            return u"\n".join(u" ".join(sentence) for sentence in internal_data["sentences"])


class CharacterTokenizedDocumentType(TokenizedDocumentType):
    """
    Simple character-level tokenized corpus. The text isn't stored in any special way,
    but is represented when read internally just as a sequence of characters in each sentence.

    If you need a more sophisticated way to handle character-type (or any non-word) units within each
    sequence, see `SegmentedLinesDocumentType`.

    """
    # TODO Update formatter and put back here
    #formatters = [("char_tokenized_doc", "pimlico.datatypes.formatters.tokenized.CharacterTokenizedDocumentFormatter")]

    class Document:
        @property
        def sentences(self):
            return self.internal_data["sentences"]

        def raw_to_internal(self, raw_data):
            return {"sentences": [list(sentence) for sentence in raw_data.split(u"\n")]}

        def internal_to_raw(self, internal_data):
            return u"\n".join(u"".join(sentence) for sentence in internal_data["sentences"])


class SegmentedLinesDocumentType(TokenizedDocumentType):
    """
    Document consisting of lines, each split into elements, which may be characters, words, or whatever.
    Rather like a tokenized corpus, but doesn't make the assumption that the elements (words in the case of a
    tokenized corpus) don't include spaces.

    You might use this, for example, if you want to train character-level models on a text corpus, but
    don't use strictly single-character units, perhaps grouping together certain short character sequences.

    Uses the character `/` to separate elements. If a `/` is found in an element, it is stored as `@slash@`,
    so this string is assumed not to be used in any element (which seems reasonable enough, generally).

    """
    # TODO Update formatter and put back here
    #formatters = [("segmented_lines", "pimlico.datatypes.formatters.tokenized.SegmentedLinesFormatter")]

    class Document:
        @property
        def sentences(self):
            return self.internal_data["sentences"]

        def raw_to_internal(self, raw_data):
            return {
                "sentences": [
                    [el.replace(u"@slash@", u"/") for el in line.split(u"/")] for line in raw_data.split(u"\n")
                ]
            }

        def internal_to_raw(self, internal_data):
            return u"\n".join(
                u"/".join(el.replace(u"/", u"@slash@") for el in line).replace(u"\n", u"")
                for line in internal_data["sentences"]
            )
