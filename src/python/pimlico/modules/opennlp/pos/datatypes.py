from pimlico.datatypes.tar import TarredCorpus


class PosTaggedCorpus(TarredCorpus):
    """
    Specialized datatype for a tarred corpus that's had POS tagging applied.

    Each document is a list of sentences. Each sentence is a list of words. Each word is a list of
    pairs (word, POS tag).

    """
    def process_document(self, data):
        return [
            [_word_tag_pair(word) for word in sentence.split(" ")] for sentence in data.split("\n")
        ]


def _word_tag_pair(text):
    word, __, tag = text.rpartition("|")
    return word, tag
