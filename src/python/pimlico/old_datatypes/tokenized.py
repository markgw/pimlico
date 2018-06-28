# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
from pimlico.old_datatypes.base import InvalidDocument
from pimlico.old_datatypes.documents import TextDocumentType
from pimlico.old_datatypes.tar import TarredCorpus, TarredCorpusWriter

__all__ = [
    "TokenizedDocumentType", "TokenizedCorpus", "TokenizedCorpusWriter",
    "SegmentedLinesDocumentType", "SegmentedLinesCorpusWriter",
    "CharacterTokenizedDocumentType", "CharacterTokenizedCorpusWriter"
]


class TokenizedDocumentType(TextDocumentType):
    formatters = [("tokenized_doc", "pimlico.datatypes.formatters.tokenized.TokenizedDocumentFormatter")]

    def process_document(self, doc, as_type=None):
        text = super(TokenizedDocumentType, self).process_document(doc)
        if as_type is not None and as_type is not TokenizedDocumentType:
            # Raw text required
            return text
        return [sentence.split(u" ") for sentence in text.split(u"\n")]


class TokenizedCorpus(TarredCorpus):
    """
    Specialized datatype for a tarred corpus that's had tokenization applied. The datatype does very little -
    the main reason for its existence is to allow modules to require that a corpus has been tokenized before
    it's given as input.

    Each document is a list of sentences. Each sentence is a list of words.

    """
    datatype_name = "tokenized"
    data_point_type = TokenizedDocumentType


class TokenizedCorpusWriter(TarredCorpusWriter):
    """
    Simple writer that takes lists of tokens and outputs them with a sentence per line and tokens separated
    by spaces.

    """
    def document_to_raw_data(self, doc):
        return u"\n".join(u" ".join(sentence) for sentence in doc)


class CharacterTokenizedDocumentType(TokenizedDocumentType):
    """
    Simple character-level tokenized corpus. The text isn't stored in any special way,
    but is represented when read internally just as a sequence of characters in each sentence.

    If you need a more sophisticated way to handle character-type (or any non-word) units within each
    sequence, see `SegmentedLinesDocumentType`.

    """
    formatters = [("char_tokenized_doc", "pimlico.datatypes.formatters.tokenized.CharacterTokenizedDocumentFormatter")]

    def process_document(self, doc, as_type=None):
        if as_type is not None and as_type not in (CharacterTokenizedDocumentType, TokenizedDocumentType):
            # Raw text required
            return super(CharacterTokenizedDocumentType, self).process_document(doc, as_type=as_type)
        return [list(sentence) for sentence in doc.split(u"\n")]


class CharacterTokenizedCorpusWriter(TarredCorpusWriter):
    """
    Simple writer that takes lists of char-tokens and outputs them with a sentence per line.
    Just joins together all the characters to store the sentence, since they can be divided up
    again when read.

    """
    def document_to_raw_data(self, doc):
        return u"\n".join(u"".join(sentence) for sentence in doc)


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
    formatters = [("segmented_lines", "pimlico.datatypes.formatters.tokenized.SegmentedLinesFormatter")]

    def process_document(self, doc, as_type=None):
        if as_type is not None and as_type not in (SegmentedLinesDocumentType, TokenizedDocumentType):
            # Raw text required
            return super(SegmentedLinesDocumentType, self).process_document(doc, as_type=as_type)
        return [[el.replace(u"@slash@", u"/") for el in line.split(u"/")]
                for line in TextDocumentType.process_document(self, doc).split(u"\n")]


class SegmentedLinesCorpusWriter(TarredCorpusWriter):
    def document_to_raw_data(self, doc):
        if isinstance(doc, InvalidDocument):
            return doc
        else:
            return u"\n".join(u"/".join(el.replace(u"/", u"@slash@") for el in line).replace(u"\n", u"") for line in doc)
