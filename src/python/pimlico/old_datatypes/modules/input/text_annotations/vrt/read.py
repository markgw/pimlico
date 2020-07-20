"""Tools for reading VRT files.

See `VRT docs <https://www.kielipankki.fi/development/korp/corpus-input-format/#VRT_file_format>`_.
"""
from pimlico.utils.core import cached_property


class VRTWord(object):
    """
    Word with all its annotations.

    The Korp docs give the following example list of positional attributes (columns):

       word form, the number of the token within the sentence, lemma, lemma with compound boundaries marked,
       part of speech, morphological analysis, dependency head number and dependency relation

    However, they are not fixed and different files may have different numbers of attributes with different
    meanings. This information is not included in the data file.

    """
    def __init__(self, word, *attributes):
        self.word = word
        self.attributes = attributes


class VRTText(object):
    """
    Contains a single VRT text (i.e. document).

    Note that VRT's structures are not hierarchical: they can be overlapping.
    See `VRT docs <https://www.kielipankki.fi/development/korp/corpus-input-format/#VRT_file_format>`_.

    We don't currently process structural attributes. This can easily be added later if necessary.

    """
    def __init__(self, words, paragraph_ranges=[], sentence_ranges=[], opening_tag=None):
        self.words = words
        self.paragraph_ranges = paragraph_ranges
        self.sentence_ranges = sentence_ranges
        self.opening_tag = opening_tag

    @staticmethod
    def from_string(data):
        lines = data.splitlines()
        # First and last lines should be "text" tags
        opening_tag = lines[0]

        # Get just the content lines, and indices of the tags
        words = []
        paragraph_ranges = []
        sentence_ranges = []

        par_open = sent_open = None
        for line in lines[1:-1]:
            # There shouldn't be any blank lines, but skip them if they arise
            if len(line.strip()) == 0:
                continue
            if line.startswith(u"<paragraph"):
                par_open = len(words)
            elif line.startswith(u"</paragraph>"):
                # If we didn't get a par opener, we can't close it, but fail quietly and skip it
                if par_open is not None:
                    paragraph_ranges.append((par_open, len(words)))
                    par_open = None
            elif line.startswith(u"<sentence"):
                sent_open = len(words)
            elif line.startswith(u"</sentence>"):
                if sent_open is not None:
                    sentence_ranges.append((sent_open, len(words)))
            else:
                # Just a normal word line
                # Don't complain about missing fields
                fields = line.rstrip(u"\n").split(u"\t")
                words.append(VRTWord(*tuple(fields)))
        return VRTText(words, paragraph_ranges, sentence_ranges, opening_tag)

    @cached_property
    def paragraphs(self):
        return [self.words[start:end] for (start, end) in self.paragraph_ranges]

    @cached_property
    def sentences(self):
        return [self.words[start:end] for (start, end) in self.sentence_ranges]

    @cached_property
    def word_strings(self):
        return [w.word for w in self.words]
