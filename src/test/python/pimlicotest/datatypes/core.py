import os
import unittest
from itertools import islice

from pimlico import TEST_DATA_DIR
from pimlico.datatypes.base import PimlicoDatatype, BaseDatatypeReader
from pimlico.datatypes.core import Dict, StringList
from pimlico.datatypes.corpora.data_points import RawTextDocumentType, TextDocumentType
from pimlico.datatypes.corpora.grouped import GroupedCorpus
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType, CharacterTokenizedDocumentType

# Create test cases automatically for lots of datatypes
DATATYPES = [
    # Specify: datatype class, path to data base dir
    (PimlicoDatatype, os.path.join(TEST_DATA_DIR, "datasets", "text_corpora", "europarl")),
    (Dict, os.path.join(TEST_DATA_DIR, "datasets", "demo_dict")),
    (StringList, os.path.join(TEST_DATA_DIR, "datasets", "demo_string_list")),
]

# Similar set of test cases, for different data point types of grouped corpora
GROUPED_CORPUS_DATATYPES = [
    # Specify: data point type instance, path to base dir, list of document attrs to test
    (RawTextDocumentType(), os.path.join(TEST_DATA_DIR, "datasets", "text_corpora", "europarl"), []),
    (TextDocumentType(), os.path.join(TEST_DATA_DIR, "datasets", "text_corpora", "europarl"), []),
    (TokenizedDocumentType(), os.path.join(TEST_DATA_DIR, "datasets", "text_corpora", "europarl"), ["sentences"]),
    (CharacterTokenizedDocumentType(), os.path.join(TEST_DATA_DIR, "datasets", "text_corpora", "europarl"), ["sentences"]),
]


class DatatypeTest(object):
    # Override the following attributes in each subclass
    datatype_cls = None
    data_base_dir = None
    datatype_args = ()
    datatype_kwargs = {}

    def setUp(self):
        # Create a dummy, empty pipeline
        # Should be called after pipeline config unit tests
        from pimlico.core.config import PipelineConfig
        self.pipeline = PipelineConfig.empty()

    def reader_tests(self, reader):
        return

    def instantiate_datatype(self):
        return self.datatype_cls()

    def runTest(self):
        # Instantiate the datatype
        datatype = self.instantiate_datatype()
        #print datatype, datatype._get_reader_cls()
        self.assertIsInstance(datatype, self.datatype_cls)
        # Create a reader setup for the given data base dir
        reader_setup = datatype([self.data_base_dir])
        self.assertIsInstance(reader_setup, BaseDatatypeReader._get_setup_cls())
        # Check that the data is ready to read from the given test data dir
        ready = reader_setup.ready_to_read()
        self.assertTrue(ready, msg="reader setup created ({}), but test data not ready to read at {}".format(
            reader_setup, self.data_base_dir
        ))
        if ready:
            # Create an actual reader
            reader = reader_setup(self.pipeline)
            self.assertIsInstance(reader, BaseDatatypeReader)
            self.assertIsInstance(reader, datatype._get_reader_cls())
            self.assertIs(reader.datatype, datatype)
            # Run further test on the reader if the subclass provides them
            self.reader_tests(reader)


class GroupedCorpusDatatypeTest(DatatypeTest):
    # Must be overridden by concrete subclasses
    data_point_type = None  # Instance of data point type
    datatype_cls = GroupedCorpus
    document_attrs = []  # Attributes to try to read on the document

    def instantiate_datatype(self):
        return self.datatype_cls(self.data_point_type)

    def reader_tests(self, reader):
        """ Additional test with a grouped corpus to try iterating, etc. """
        # Try reading several documents from the reader
        for doc_name, doc in islice(reader, 3):
            # Check we can reader the raw_data attribute, which all doc types should have
            self.assertIsInstance(doc.raw_data, unicode)
            # Internal data should always be available in some form, though its keys may vary
            self.assertIsInstance(doc.internal_data, dict)
            # Try reading any attributes that this doc type is supposed to have
            for attr in self.document_attrs:
                # Check the attr exists
                self.assertTrue(hasattr(doc, attr))
                if hasattr(doc, attr):
                    # Try reading the attribute: usually this is a property, which could fail
                    getattr(doc, attr)


for datatype_cls, base_dir in DATATYPES:
    cls_name = "{}Test".format(datatype_cls.__name__)
    # Put the test class in globals so that unittest can discover it

    # This is just like doing the following:
    #
    #   class <Datatype>Test(DatatypeTest, unittest.TestCase):
    #       datatype_cls = datatype_cls
    #       data_base_dir = base_dir

    globals()[cls_name] = type(
        cls_name,
        (DatatypeTest, unittest.TestCase),
        {
            "datatype_cls": datatype_cls,
            "data_base_dir": base_dir,
        }
    )

for data_point_type, base_dir, doc_attrs in GROUPED_CORPUS_DATATYPES:
    cls_name = "GroupedCorpus{}Test".format(data_point_type.name)
    # Put the test class in globals so that unittest can discover it

    # This is just like doing the following:
    #
    #   class <Datatype>Test(DatatypeTest, unittest.TestCase):
    #       datatype_cls = datatype_cls
    #       data_base_dir = base_dir

    globals()[cls_name] = type(
        cls_name,
        (GroupedCorpusDatatypeTest, unittest.TestCase),
        {
            "data_point_type": data_point_type,
            "data_base_dir": base_dir,
            "document_attrs": doc_attrs,
        }
    )


if __name__ == "__main__":
    tester = unittest.main()
