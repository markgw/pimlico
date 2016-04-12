import json

from pimlico.core.modules.map import skip_invalid
from pimlico.datatypes.jsondoc import JsonDocumentCorpus, JsonDocumentCorpusWriter
from pimlico.datatypes.tar import pass_up_invalid
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, WordAnnotationCorpusWriter


class StanfordDependencyParseCorpus(JsonDocumentCorpus):
    datatype_name = "stanford_dependency_parses"

    @skip_invalid
    def process_document(self, data):
        data = super(CoNLLDependencyParseCorpus, self).process_document(data)
        if data.strip():
            # Read in the dep parse trees as JSON and return a dep parse data structure
            return [StanfordDependencyParse.from_json(sentence_json) for sentence_json in data]
        else:
            return []


class StanfordDependencyParseCorpusWriter(JsonDocumentCorpusWriter):
    @pass_up_invalid
    def document_to_raw_data(self, doc):
        # Data should be a list of StanfordDependencyParses, one for each sentence
        return super(CoNLLDependencyParseInputCorpusWriter, self).document_to_raw_data(
            [parse.to_json_list() for parse in doc]
        )


class StanfordDependencyParse(object):
    def __init__(self, dependencies):
        self.dependencies = dependencies

    @staticmethod
    def from_json(json):
        """
        Read in from JSON, as received from the Stanford CoreNLP server output. Input should be parsed JSON.

        """
        return StanfordDependencyParse([StanfordDependency.from_json(dep_json) for dep_json in json])

    @staticmethod
    def from_json_string(data):
        return StanfordDependencyParse.from_json(json.loads(data))

    def to_json_list(self):
        return [dep.to_json_dict() for dep in self.dependencies]


class StanfordDependency(object):
    def __init__(self, dep, dependent_index, governor_index, dependent_gloss, governor_gloss):
        self.dep = dep
        self.dependent_index = dependent_index
        self.governor_index = governor_index
        self.dependent_gloss = dependent_gloss
        self.governor_gloss = governor_gloss

    @staticmethod
    def from_json(json):
        return StanfordDependency(
            json["dep"], json["dependent"], json["governor"], json["dependentGloss"], json["governorGloss"]
        )

    def to_json_dict(self):
        return {
            "dep": self.dep,
            "dependent": self.dependent_index,
            "dependentGloss": self.dependent_gloss,
            "governor": self.governor_index,
            "governorGloss": self.governor_gloss,
        }


def _usnone(field, typ=lambda x:x):
    return None if field == "_" else typ(field)


def _noneus(field):
    return "_" if field is None else unicode(field)


class CoNLLDependencyParseCorpus(WordAnnotationCorpus):
    datatype_name = "conll_dependency_parses"

    @skip_invalid
    def process_document(self, data):
        data = super(CoNLLDependencyParseCorpus, self).process_document(data)
        return [
            [
                [
                    # ID,          word,     lemma,             cpostag,  postag,   feats,
                    int(token[0]), token[1], _usnone(token[2]), token[3], token[4], _usnone(token[5]),
                    # head,                 deprel,             phead,                 pdeprel
                    _usnone(token[6], int), _usnone(token[7]), _usnone(token[8], int), _usnone(token[9])
                ] for token in sentence
            ] for sentence in data
        ]


class CoNLLDependencyParseCorpusWriter(WordAnnotationCorpusWriter):
    def __init__(self, base_dir, **kwargs):
        super(CoNLLDependencyParseCorpusWriter, self).__init__(
            # Blank line between sentences
            u"\n\n",
            # Single linebreak between words
            u"\n",
            # Tab-separated fields
            u"{id}\t{word}\t{lemma}\t{cpostag}\t{postag}\t{feats}\t{head}\t{deprel}\t{phead}\t{pdeprel}",
            # No linebreaks or tabs in words
            u"\n\t",
            base_dir, **kwargs
        )

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        """
        Data should be a list of sentences
        Each sentence is a list of tokens.
        Each token is a list of columns (fields).

        """
        return super(CoNLLDependencyParseCorpusWriter, self).document_to_raw_data(
            u"\n\n".join(
                u"\n".join(
                    # Replace Nones with underscores
                    u"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % tuple(map(_noneus, token)) for token in sentence
                ) for sentence in doc
            )
        )


class CoNLLDependencyParseInputCorpus(WordAnnotationCorpus):
    """
    The version of the CoNLL format (conllx) that only has the first 6 columns, i.e. no dependency parse yet annotated.

    """
    datatype_name = "conll_dependency_parse_inputs"

    @skip_invalid
    def process_document(self, data):
        data = super(CoNLLDependencyParseInputCorpus, self).process_document(data)
        return [
            [
                [
                    # ID,          word,     lemma,             cpostag,  postag,   feats,
                    int(token[0]), token[1], _usnone(token[2]), token[3], token[4], _usnone(token[5]),
                ] for token in sentence
            ] for sentence in data
        ]


class CoNLLDependencyParseInputCorpusWriter(WordAnnotationCorpusWriter):
    def __init__(self, base_dir, **kwargs):
        super(CoNLLDependencyParseInputCorpusWriter, self).__init__(
            # Blank line between sentences
            u"\n\n",
            # Single linebreak between words
            u"\n",
            # Tab-separated fields
            u"{id}\t{word}\t{lemma}\t{cpostag}\t{postag}\t{feats}",
            # No linebreaks or tabs in words
            u"\n\t",
            base_dir, **kwargs
        )

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        """
        Data should be a list of sentences
        Each sentence is a list of tokens.
        Each token is a list of columns (fields).

        """
        return super(CoNLLDependencyParseInputCorpusWriter, self).document_to_raw_data(
            u"\n\n".join(
                u"\n".join(
                    # Replace Nones with underscores
                    u"%s\t%s\t%s\t%s\t%s\t%s" % tuple(map(_noneus, token)) for token in sentence
                ) for sentence in doc
            )
        )
