from cStringIO import StringIO

from pimlico.core.modules.map import skip_invalid
from pimlico.datatypes.tar import TarredCorpusWriter, pass_up_invalid, TarredCorpus


class CandcOutputCorpus(TarredCorpus):
    datatype_name = "candc_output"

    @skip_invalid
    def process_document(self, data):
        data = super(CandcOutputCorpus, self).process_document(data)
        return CandcOutput(data)


class CandcOutputCorpusWriter(TarredCorpusWriter):
    @pass_up_invalid
    def document_to_raw_data(self, doc):
        # Data should be a CandcOutput
        return doc.raw_data


class CandcOutput(object):
    """
    C&C output is kept as raw text, since we just want to store it as it comes out from the parser.
    We only pull it apart when it's needed.

    """
    def __init__(self, raw_data):
        self.raw_data = raw_data

    def __iter__(self):
        # Remove the comments, plus the next line (which is empty) from the beginning of the file
        s = StringIO(self.raw_data)
        for l in s:
            if not l.startswith("#"):
                break
        data = s.getvalue()
        # Now the rest is sentences, separated by blank lines
        for sentence_data in data.split("\n\n"):
            sentence_data = sentence_data.strip("\n ")
            if sentence_data:
                # Wrap each sentence up in an object that helps us pull it apart
                yield CandcSentence(sentence_data)


class CandcSentence(object):
    def __init__(self, data):
        self.data = data

    def split_grs_and_tag_line(self):
        # Should be the last line of the data and start with <c>
        grs,__, tag_line = self.data.rpartition("\n")
        if tag_line.startswith("<c>"):
            # GRs may be empty
            return grs if grs.strip("\n ") else None, tag_line
        else:
            # Seems to be no tag line
            return self.data, None

    @property
    def tag_line(self):
        return self.split_grs_and_tag_line()[1]

    @property
    def grs(self):
        return self.split_grs_and_tag_line()[0]