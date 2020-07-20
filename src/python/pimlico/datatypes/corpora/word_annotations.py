"""
Textual corpus type where each word is accompanied by some annotations.

"""
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType
from pimlico.utils.core import cached_property

SENTENCE_DIVIDER = "\n<SENT>\n"


def _encode_token(tok):
    """
    Replace any linebreaks and tabs
    """
    return tok.replace("\n", "<LINEBREAK>").replace("\t", "<TAB>")


def _decode_token(tok):
    return tok.replace("<LINEBREAK>", "\n").replace("<TAB>", "\t")


class WordAnnotationsDocumentType(TokenizedDocumentType):
    """
    List of sentences, each consisting of a list of word, each consisting of a
    tuple of the token and its annotations.

    Using this type directly gives documents with annotations per word, but doesn't
    know what the annotations are. Currently there's no way to perform type checking
    to ensure that a given set of annotations are included.

    This is not very satisfactory, but will do for now.

    """
    class Document(object):
        keys = ["word_annotations"]

        @cached_property
        def text(self):
            return "\n".join(" ".join(word for word in sentence) for sentence in self.sentences)

        @cached_property
        def sentences(self):
            return [[word[0] for word in sentence] for sentence in self.internal_data["word_annotations"]]

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
