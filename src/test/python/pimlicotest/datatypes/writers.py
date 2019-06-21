"""
Tests creating writers for various datatypes and writing
out some data.

Typically the data is created programmatically,
so this tests the writing routines that convert it to
some serializable format and write it out to disk.

If you set the environment variable ``KEEP_OUTPUT=1``, the
output will not be removed after the test is complete. This
can be useful for using the writer tests to generate
datasets for corresponding reader tests.

"""
from __future__ import print_function
import shutil
import unittest
from tempfile import mkdtemp

import os

from pimlico.core.config import PipelineConfig
from pimlico.datatypes.core import Dict, StringList
from pimlico.datatypes.dictionary import DictionaryData, Dictionary
from pimlico.datatypes.embeddings import Embeddings
from pimlico.datatypes.files import NamedFileCollection, NamedFile, TextFile


class WriterTest(object):
    """
    Base class for routines shared between test cases.

    """
    # Should be overridden by subclasses
    datatype_cls = None

    def write_data(self, writer):
        # Subclasses should override, or override test_write() instead
        raise NotImplementedError()

    def setUp(self):
        # Prepare a directory to output to
        self.output_dir = mkdtemp()

    def tearDown(self):
        # Remove the temporary dir with output
        # Allow an environment variable to control whether we remove the output
        keep_output = bool(len(os.environ.get("KEEP_OUTPUT", "")))
        if keep_output:
            print("Leaving output from {} in {}".format(type(self).__name__, self.output_dir))
        else:
            shutil.rmtree(self.output_dir)

    def instantiate_datatype(self):
        """ Subclasses may override if the datatype needs any special args, or similar. """
        return self.datatype_cls()

    def get_writer(self, **kwargs):
        # Create an empty pipeline
        pipeline = PipelineConfig.empty()
        # Instantiate the datatype
        datatype = self.instantiate_datatype()
        # Make a writer to write data to
        # We return the writer, which should be used as a context manager
        return datatype.get_writer(self.output_dir, pipeline, **kwargs)

    def test_write(self):
        with self.get_writer() as writer:
            self.write_data(writer)


class DictionaryWriterTest(WriterTest, unittest.TestCase):
    datatype_cls = Dictionary

    def write_data(self, writer):
        # Prepare data
        data = DictionaryData()
        data.add_documents([
            "here is some data".split(),
            "i'm adding some data to the dictionary".split(),
            "the dictionary includes several documents".split(),
            "the documents include several words".split(),
            "the words exhibit some overall between documents".split()
        ])
        # Replace the writer's empty dictionary with this one
        writer.data = data


class DictWriterTest(WriterTest, unittest.TestCase):
    datatype_cls = Dict

    def write_data(self, writer):
        writer.write_dict({
            "some key": "some string",
            "another key, int": 12345,
            "and a float": 0.5,
            "and even another dict": {
                "next level": "also has data",
            },
        })


class StringListWriterTest(WriterTest, unittest.TestCase):
    datatype_cls = StringList

    def write_data(self, writer):
        writer.write_list(
            ["a", "list", "of", "strings", ",", "quite", "simply"]
        )


class NamedFileCollectionWriterTest1(WriterTest, unittest.TestCase):
    datatype_cls = NamedFileCollection

    def instantiate_datatype(self):
        return self.datatype_cls(["text_file.txt"])

    def write_data(self, writer):
        writer.write_file(writer.filenames[0], "Some text data in a single text file\n\nJust some text\n")


class NamedFileCollectionWriterTest2(WriterTest, unittest.TestCase):
    datatype_cls = NamedFileCollection

    def instantiate_datatype(self):
        return self.datatype_cls(["text_file.txt", "data.bin"])

    def write_data(self, writer):
        import struct
        # Write a text file
        writer.write_file(writer.filenames[0], "Some text data in a single text file\n\nJust some text\n")
        # Also write some binary data
        data = struct.pack("?fff", True, 0.5, 1.0, 2.0)
        writer.write_file(writer.filenames[1], data)


class NamedFileWriterTest(WriterTest, unittest.TestCase):
    datatype_cls = NamedFile

    def instantiate_datatype(self):
        return self.datatype_cls("text_file.txt")

    def write_data(self, writer):
        # Write a text file
        writer.write_file("Some text data in a single text file\n\nJust some text\nThis one's for a NamedFile test\n")


class TextFileWriterTest(WriterTest, unittest.TestCase):
    datatype_cls = TextFile

    def write_data(self, writer):
        # Write a text file
        writer.write_file("Some text data in a single text file\n\nJust some text\nThis one's for a TextFile test\n")


class EmbeddingsWriterTest(WriterTest, unittest.TestCase):
    datatype_cls = Embeddings

    def write_data(self, writer):
        import numpy
        # 10 random vectors, dimensionality 50
        vectors = numpy.random.rand(10, 50)
        # Need a word for each vectors
        words = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
        counts = list(range(10))

        writer.write_vectors(vectors)
        writer.write_word_counts(zip(words, counts))
