# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import unicode_literals
from builtins import object

from pimlico.cli.browser.tools.formatter import DocumentBrowserFormatter
from pimlico.datatypes.corpora.data_points import TextDocumentType
from pimlico.utils.core import cached_property

__all__ = ["TokenizedDocumentType", "SegmentedLinesDocumentType", "CharacterTokenizedDocumentType"]


class TokenizedDocumentType(TextDocumentType):
    """
    Specialized data point type for documents that have had tokenization applied.
    It does very little processing - the main reason for its existence is to allow
    modules to require that a corpus has been tokenized before it's given as input.

    Each document is a list of sentences. Each sentence is a list of words.

    """
    formatters = [("tokenized_doc", "pimlico.datatypes.corpora.tokenized.TokenizedDocumentFormatter")]
    data_point_type_supports_python2 = True

    class Document(object):
        keys = ["sentences"]

        @cached_property
        def text(self):
            if self._raw_data is not None:
                # The text is just the raw data, decoded, so it's quickest to get it from that
                return self._raw_data.decode("utf-8")
            else:
                return "\n".join(" ".join(sentence) for sentence in self.internal_data["sentences"])

        def raw_to_internal(self, raw_data):
            return {
                "sentences": [sentence.split(" ") for sentence in raw_data.decode("utf-8").split("\n")],
            }

        def internal_to_raw(self, internal_data):
            return bytes("\n".join(" ".join(sentence) for sentence in internal_data["sentences"]).encode("utf-8"))


class TokenizedDocumentFormatter(DocumentBrowserFormatter):
    """
    Format a tokenized document by putting sentences on consecutive lines
    and separating tokens with spaces.

    """
    DATATYPE = TokenizedDocumentType()

    def format_document(self, doc):
        return "\n".join(" ".join(sent) for sent in doc.sentences)


class LemmatizedTokensDocumentType(TokenizedDocumentType):
    """
    Identical to :class:`TokenizedDocumentType`. Separate subclass to allow
    modules to require that their input has been lemmatized (and tokenized).

    """
    data_point_type_supports_python2 = True


class CharacterTokenizedDocumentType(TokenizedDocumentType):
    """
    Simple character-level tokenized corpus. The text isn't stored in any special way,
    but is represented when read internally just as a sequence of characters in each sentence.

    If you need a more sophisticated way to handle character-type (or any non-word) units within each
    sequence, see `SegmentedLinesDocumentType`.

    """
    data_point_type_supports_python2 = True

    class Document(object):
        @property
        def sentences(self):
            return self.internal_data["sentences"]

        def raw_to_internal(self, raw_data):
            text = raw_data.decode("utf-8")
            return {
                "sentences": [list(sentence) for sentence in text.split("\n")],
                "text": text,
            }

        def internal_to_raw(self, internal_data):
            return bytes("\n".join("".join(sentence) for sentence in internal_data["sentences"]).encode("utf-8"))


class SegmentedLinesDocumentType(TokenizedDocumentType):
    """
    Document consisting of lines, each split into elements, which may be characters, words, or whatever.
    Rather like a tokenized corpus, but doesn't make the assumption that the elements (words in the case of a
    tokenized corpus) don't include spaces.

    You might use this, for example, if you want to train character-level models on a text corpus, but
    don't use strictly single-character units, perhaps grouping together certain short character sequences.

    Uses the character `/` to separate elements in the raw data.
    If a `/` is found in an element, it is stored as `@slash@`,
    so this string is assumed not to be used in any element (which seems reasonable enough, generally).

    """
    data_point_type_supports_python2 = True

    class Document(object):
        @property
        def text(self):
            return u"\n".join(u"".join(token for token in sent) for sent in self.internal_data["sentences"])

        @property
        def sentences(self):
            return self.internal_data["sentences"]

        def raw_to_internal(self, raw_data):
            sentences = [[el.replace("@slash@", "/") for el in line.split("/")] for line in raw_data.decode("utf-8").split("\n")]
            return {
                "sentences": sentences,
                # For producing the "text" attribute, we assume it makes sense to join on the empty string
                "text": "\n".join("".join(line) for line in sentences)
            }

        def internal_to_raw(self, internal_data):
            return bytes("\n".join(
                "/".join(el.replace("/", "@slash@") for el in line).replace("\n", "")
                for line in internal_data["sentences"]
            ).encode("utf-8"))
