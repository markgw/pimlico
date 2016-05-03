"""
TODO Parse tress are temporary implementations that don't actually parse the data, but just split it into
 sentences.
"""
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid


class ConstituencyParseTreeCorpus(TarredCorpus):
    """
    Note that this is not fully developed yet. At the moment, you'll just get, for each document, a list of the
    texts of each tree. In future, they will be better represented.

    """
    datatype_name = "parse_trees"

    def process_document(self, data):
        if data.strip():
            # TODO This should read in the parse trees and return a tree data structure
            return data.split("\n\n")
        else:
            return []


class ConstituencyParseTreeCorpusWriter(TarredCorpusWriter):
    @pass_up_invalid
    def document_to_raw_data(self, doc):
        # Put a blank line between every parse
        return "\n\n".join(doc)
