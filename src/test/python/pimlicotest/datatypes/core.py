"""
Large set of unit tests for core datatypes.

Tests instantiating the datatypes and reading in data from an example dataset.

"""
from builtins import str, bytes
from builtins import object
import os
import types
import unittest
from itertools import islice

from pimlico import TEST_DATA_DIR

# Create test cases automatically for lots of datatypes
from pimlico.datatypes.base import PimlicoDatatype
from pimlico.datatypes.core import Dict, StringList
from pimlico.datatypes.corpora import InvalidDocument
from pimlico.datatypes.corpora.data_points import RawTextDocumentType, TextDocumentType
from pimlico.datatypes.corpora.floats import FloatListDocumentType, FloatListsDocumentType
from pimlico.datatypes.corpora.grouped import GroupedCorpus
from pimlico.datatypes.corpora.ints import IntegerListDocumentType, IntegerListsDocumentType
from pimlico.datatypes.corpora.table import IntegerTableDocumentType
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType, CharacterTokenizedDocumentType
from pimlico.datatypes.dictionary import Dictionary
from pimlico.datatypes.embeddings import Embeddings
from pimlico.datatypes.files import NamedFileCollection, NamedFile, TextFile

DATATYPES = [
    # Specify: datatype class, path to data base dir, list of attributes/methods to test
    (PimlicoDatatype(), os.path.join("text_corpora", "europarl"), []),
    (Dict(), "demo_dict", ["get_dict"]),
    (StringList(), "demo_string_list", ["get_list"]),
    (Dictionary(), "dictionary", ["get_data"]),
    (NamedFileCollection(["text_file.txt"]), "named_files1", [("read_file", 0)]),
    (
        NamedFileCollection(["text_file.txt", "data.bin"]), "named_files2",
        [("read_file", 0), ("read_file", 1)]
    ),
    # This test uses the same dataset as the NamedFileCollection with one file
    (NamedFile("text_file.txt"), "named_files1", ["read_file"]),
    # This test uses a dataset written by a NamedFile writer
    (NamedFile("text_file.txt"), "named_file", ["read_file"]),
    (TextFile(), "text_file", ["read_file"]),
    (Embeddings(), "embeddings", ["vectors", "word_counts"]),
]

# Similar set of test cases, for different data point types of grouped corpora
GROUPED_CORPUS_DATATYPES = [
    # Specify: data point type instance, path to base dir, list of document attrs to test
    (RawTextDocumentType(), os.path.join("text_corpora", "europarl"), []),
    (TextDocumentType(), os.path.join("text_corpora", "europarl"), []),
    (TokenizedDocumentType(), os.path.join("text_corpora", "europarl"), ["sentences"]),
    (CharacterTokenizedDocumentType(), os.path.join("text_corpora", "europarl"), ["sentences"]),
    (IntegerTableDocumentType(), os.path.join("corpora", "int_table"), ["table"]),
    (IntegerListDocumentType(), os.path.join("corpora", "int_list"), ["list"]),
    (IntegerListsDocumentType(), os.path.join("corpora", "int_lists"), ["lists"]),
    (FloatListDocumentType(), os.path.join("corpora", "float_list"), ["list"]),
    (FloatListsDocumentType(), os.path.join("corpora", "float_lists"), ["lists"]),
]


class DatatypeTest(object):
    """
    Base class for datatype tests, providing routines in common to all of them.
    This is dynamically subclassed below for each datatype to create test cases
    for each one.

    """
    # Override the following attributes in each subclass
    datatype = None
    data_base_dir = None
    datatype_args = ()
    datatype_kwargs = {}
    attrs_to_test = []

    def setUp(self):
        # Create a dummy, empty pipeline
        # Should be called after pipeline config unit tests
        from pimlico.core.config import PipelineConfig
        self.pipeline = PipelineConfig.empty()

    def reader_tests(self, reader):
        datatype_name = reader.datatype.full_datatype_name()

        for attr in self.attrs_to_test:
            if type(attr) is tuple:
                # Allow args to be specified for a method call, optionally
                attr, args = attr
                if type(args) is not tuple:
                    # Simple case for a single arg
                    args = (args, )
            else:
                args = tuple()

            # If the attr is a property or simply an attribute, this is all we need to do
            try:
                value = getattr(reader, attr)
            except AttributeError:
                raise AssertionError("datatype {} does not have an attribute '{}', named in test definition".format(
                    datatype_name, attr
                ))
            except Exception as e:
                raise AssertionError("error getting attribute '{}' of {}: {}".format(attr, datatype_name, e))
            # If it's a method, we should call it
            if type(value) is types.MethodType:
                try:
                    value = value(*args)
                except Exception as e:
                    raise AssertionError("error calling method {}({}) on datatype {}: {}".format(
                        attr, ", ".join(str(a) for a in args), datatype_name, e)
                    )

    def runTest(self):
        datatype = self.datatype
        # Create a reader setup for the given data base dir
        reader_setup = datatype([self.data_base_dir])
        self.assertIsInstance(reader_setup, PimlicoDatatype.Reader.Setup)
        # Check that the data is ready to read from the given test data dir
        ready = reader_setup.ready_to_read()
        self.assertTrue(ready, msg="reader setup created ({}), but test data not ready to read at {}".format(
            reader_setup, self.data_base_dir
        ))
        if ready:
            # Create an actual reader
            reader = reader_setup(self.pipeline)
            self.assertIsInstance(reader, PimlicoDatatype.Reader)
            self.assertIsInstance(reader, datatype.Reader)
            self.assertIs(reader.datatype, datatype)
            # Run further test on the reader if the subclass provides them
            self.reader_tests(reader)


class GroupedCorpusDatatypeTest(DatatypeTest):
    # Must be overridden by concrete subclasses
    datatype = None
    document_attrs = []  # Attributes to try to read on the document

    def reader_tests(self, reader):
        """ Additional test with a grouped corpus to try iterating, etc. """
        super(GroupedCorpusDatatypeTest, self).reader_tests(reader)
        # Try reading several documents from the reader
        for doc_name, doc in islice(reader, 3):
            # Check we can reader the raw_data attribute, which all doc types should have
            # Note that this should be a string, which may be encoded unicode or some other string data
            self.assertIsInstance(doc.raw_data, bytes)
            # Internal data should always be available in some form, though its keys may vary
            self.assertIsInstance(doc.internal_data, dict)
            # Example corpora shouldn't generally include invalid documents, so it's a sign something has gone wrong
            self.assertNotIsInstance(doc, InvalidDocument.Document,
                                     msg="{} corpus contained invalid doc...\nError was: {}".format(
                                         reader.datatype.data_point_type.name,
                                         getattr(doc, "error_info", "(none)")
                                     ))
            # Try reading any attributes that this doc type is supposed to have
            for attr in self.document_attrs:
                # Check the attr exists
                self.assertTrue(hasattr(doc, attr), msg="attribute '{}' does not exist on data point type {}".format(
                    attr, self.datatype.data_point_type.name
                ))
                if hasattr(doc, attr):
                    # Try reading the attribute: usually this is a property, which could fail
                    getattr(doc, attr)


_used_names = []
for datatype, base_dir, attrs_to_test in DATATYPES:
    base_cls_name = cls_name = "{}Test".format(type(datatype).__name__)
    # Allow multiple tests of the same datatype without name clashes
    name_id = -1
    while cls_name in _used_names:
        name_id += 1
        cls_name = "{}{}".format(base_cls_name, name_id)
    _used_names.append(cls_name)

    if not os.path.isabs(base_dir):
        base_dir = os.path.join(TEST_DATA_DIR, "datasets", base_dir)
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
            "datatype": datatype,
            "data_base_dir": base_dir,
            "attrs_to_test": attrs_to_test,
        }
    )

for data_point_type, base_dir, doc_attrs in GROUPED_CORPUS_DATATYPES:
    base_cls_name = cls_name = "GroupedCorpus{}Test".format(data_point_type.name)
    # Allow multiple tests of the same datatype without name clashes
    name_id = -1
    while cls_name in _used_names:
        name_id += 1
        cls_name = "{}{}".format(base_cls_name, name_id)
    _used_names.append(cls_name)

    if not os.path.isabs(base_dir):
        base_dir = os.path.join(TEST_DATA_DIR, "datasets", base_dir)
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
            "datatype": GroupedCorpus(data_point_type),
            "data_base_dir": base_dir,
            "document_attrs": doc_attrs,
        }
    )


if __name__ == "__main__":
    tester = unittest.main()
