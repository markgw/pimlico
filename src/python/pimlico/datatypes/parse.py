from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter


class ConstituencyParseTreeCorpus(TarredCorpus):
    """
    Note that this is not fully developed yet. At the moment, you'll just get, for each document, a list of the
    texts of each tree. In future, they will be better represented.

    """
    def process_document(self, data):
        if data.strip():
            # TODO This should read in the parse trees and return a tree data structure
            return data.split("\n\n")
        else:
            return []


class ConstituencyParseTreeCorpusWriter(TarredCorpusWriter):
    def add_document(self, archive_name, doc_name, data):
        # Put a blank line between every parse
        data = "\n\n".join(data)
        super(ConstituencyParseTreeCorpusWriter, self).add_document(archive_name, doc_name, data)
