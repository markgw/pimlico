"""
TODO These are all temporary implementations that don't actually parse the data, but just split it into
 sentences.
"""
import json

from pimlico.core.modules.map import skip_invalid
from pimlico.datatypes.jsondoc import JsonDocumentCorpusWriter, JsonDocumentCorpus
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid


class ConstituencyParseTreeCorpus(TarredCorpus):
    """
    Note that this is not fully developed yet. At the moment, you'll just get, for each document, a list of the
    texts of each tree. In future, they will be better represented.

    """
    @skip_invalid
    def process_document(self, data):
        if data.strip():
            # TODO This should read in the parse trees and return a tree data structure
            return data.split("\n\n")
        else:
            return []


class ConstituencyParseTreeCorpusWriter(TarredCorpusWriter):
    @pass_up_invalid
    def add_document(self, archive_name, doc_name, data):
        # Put a blank line between every parse
        data = "\n\n".join(data)
        super(ConstituencyParseTreeCorpusWriter, self).add_document(archive_name, doc_name, data)


class DependencyParseCorpus(JsonDocumentCorpus):
    """
    Note that this is not fully developed yet. At the moment, you'll just get, for each document, a list of the
    texts of each tree. In future, they will be better represented.

    """
    @skip_invalid
    def process_document(self, data):
        data = super(DependencyParseCorpus, self).process_document(data)
        if data.strip():
            # Read in the dep parse trees as JSON and return a dep parse data structure
            return [StanfordDependencyParse.from_json(sentence_json) for sentence_json in data]
        else:
            return []


class DependencyParseCorpusWriter(JsonDocumentCorpusWriter):
    @pass_up_invalid
    def add_document(self, archive_name, doc_name, data):
        # Data should be a list of StanfordDependencyParses, one for each sentence
        data = [parse.to_json_list() for parse in data]
        super(DependencyParseCorpusWriter, self).add_document(archive_name, doc_name, data)


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
