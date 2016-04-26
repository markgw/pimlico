from pimlico.datatypes.tar import TarredCorpus


class TokenizedCorpus(TarredCorpus):
    """
    Specialized datatype for a tarred corpus that's had tokenization applied. The datatype does very little -
    the main reason for its existence is to allow modules to require that a corpus has been tokenized before
    it's given as input.

    Each document is a list of sentences. Each sentence is a list of words.

    """
    datatype_name = "tokenized"

    def process_document(self, data):
        return [
            sentence.split(" ") for sentence in data.split("\n")
        ]
