import os
import unittest
from itertools import islice

from pimlico import TEST_DATA_DIR
from pimlico.datatypes.corpora.data_points import RawTextDocumentType
from pimlico.datatypes.corpora.grouped import GroupedCorpus
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class PimlicoDatatypeTest(unittest.TestCase):
    def setUp(self):
        # TODO
        pass

    def run_test(self):
        # TODO
        pass


if __name__ == "__main__":
    #unittest.main()

    # TODO The following should be turned into a unittest, or a series
    # For now I'm in such early stages of writing the code that I just need to try it simply

    from pimlico.datatypes.base import PimlicoDatatype
    print "Imported datatype class"
    base_datatype = PimlicoDatatype()

    # Create a dummy, empty pipeline
    from pimlico.core.config import PipelineConfig
    pipeline = PipelineConfig.empty()

    base_dir = os.path.join(TEST_DATA_DIR, "datasets", "text_corpora", "europarl")
    print "Creating reader for {} as base datatype ({})".format(base_dir, base_datatype)
    reader = base_datatype(base_dir, pipeline)
    print "Created reader: {}".format(reader)

    print "Treating data as raw text iterable corp"
    gcorp_datatype = GroupedCorpus(RawTextDocumentType())

    reader = gcorp_datatype(base_dir, pipeline)
    print "Created reader: {}".format(reader)

    print "Reading some data"
    for doc_name, doc in islice(reader, 5):
        print
        print doc_name, doc
        print doc.raw_data[:10]

    print "Treating data as simple tokenized text iterable corp"
    tok_corp_datatype = GroupedCorpus(TokenizedDocumentType())

    reader = tok_corp_datatype(base_dir, pipeline)
    print "Created reader: {}".format(reader)

    print "Reading some data"
    for doc_name, doc in islice(reader, 5):
        print
        print doc_name, doc
        print doc.raw_data[:10]
        print doc.sentences[:2]
