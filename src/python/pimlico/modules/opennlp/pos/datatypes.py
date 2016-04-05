from pimlico.datatypes.word_annotations import WordAnnotationCorpus, SimpleWordAnnotationCorpusWriter


class PosTaggedCorpus(WordAnnotationCorpus):
    """
    Specialized datatype for a tarred corpus that's had POS tagging applied.

    Each document is a list of sentences. Each sentence is a list of words. Each word is a dict including the
    word and its POS tag.

    """
    datatype_name = "pos"

    annotation_fields = ["word", "pos"]


class PosTaggedCorpusWriter(SimpleWordAnnotationCorpusWriter):
    def __init__(self, base_dir, **kwargs):
        super(PosTaggedCorpusWriter, self).__init__(base_dir, ["word", "pos"], **kwargs)
