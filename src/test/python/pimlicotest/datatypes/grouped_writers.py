"""
Writer test cases for grouped corpora with different data point types.

"""
from __future__ import division
from builtins import range
import random
import string
import unittest

from pimlico.datatypes.corpora.data_points import RawDocumentType
from pimlico.datatypes.corpora.floats import FloatListsDocumentType, FloatListDocumentType
from pimlico.datatypes.corpora.grouped import GroupedCorpus
from pimlico.datatypes.corpora.ints import IntegerListDocumentType, IntegerListsDocumentType
from pimlico.datatypes.corpora.table import IntegerTableDocumentType
from .writers import WriterTest


class GroupedCorpusWriterTest(WriterTest):
    datatype_cls = GroupedCorpus
    # Subclasses should override this with the data point type instance
    data_point_type = None

    def instantiate_datatype(self):
        return GroupedCorpus(self.data_point_type)

    def write_data(self, writer):
        # If the test gives us enough documents, change the archive name after every 5
        archive_base_name = "archive_{:02d}"

        for doc_num, (doc_name, doc) in enumerate(self.get_documents()):
            writer.add_document(
                archive_base_name.format(doc_num // 5),
                doc_name,
                doc
            )

    def get_documents(self):
        """
        Should be overridden by subclasses to produce an iterator over
        document instances, each with a name, yielded as (doc_name, doc).

        """
        raise NotImplementedError()


class RawDocumentTypeWriterTest(GroupedCorpusWriterTest, unittest.TestCase):
    data_point_type = RawDocumentType()

    def get_documents(self):
        for i in range(15):
            # Generate a random string for this document
            data = u"".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(50))
            name = u"".join(random.choice(string.ascii_uppercase) for _ in range(10))
            yield name, RawDocumentType()(raw_data=data)


class IntegerTableTypeWriterTest(GroupedCorpusWriterTest, unittest.TestCase):
    data_point_type = IntegerTableDocumentType()

    def get_writer(self):
        # Set the row length in the metadata
        return super(IntegerTableTypeWriterTest, self).get_writer(row_length=10)

    def get_documents(self):
        for i in range(15):
            # Generate a random table for this document
            table = [
                [random.randint(0, 10) for colnum in range(10)]
                for rownum in range(10)
            ]
            name = u"".join(random.choice(string.ascii_uppercase) for _ in range(10))
            yield name, self.data_point_type(table=table)


class IntegerListsTypeWriterTest(GroupedCorpusWriterTest, unittest.TestCase):
    data_point_type = IntegerListsDocumentType()

    def get_documents(self):
        for i in range(15):
            # Generate a random table for this document
            lsts = [
                [random.randint(0, 10) for colnum in range(random.randint(0, 20))]
                # Each row has a random length and there's a random number of rows
                for rownum in range(random.randint(0, 20))
            ]
            name = u"".join(random.choice(string.ascii_uppercase) for _ in range(10))
            yield name, self.data_point_type(lists=lsts)


class IntegerListTypeWriterTest(GroupedCorpusWriterTest, unittest.TestCase):
    data_point_type = IntegerListDocumentType()

    def get_documents(self):
        for i in range(15):
            # Generate a random table for this document
            # Each doc has a random length
            lst = [random.randint(0, 10) for i in range(random.randint(0, 20))]
            name = u"".join(random.choice(string.ascii_uppercase) for _ in range(10))
            yield name, self.data_point_type(list=lst)


class FloatListsTypeWriterTest(GroupedCorpusWriterTest, unittest.TestCase):
    data_point_type = FloatListsDocumentType()

    def get_documents(self):
        for i in range(15):
            # Generate a random table for this document
            lsts = [
                [random.uniform(0., 10.) for colnum in range(random.randint(0, 20))]
                # Each row has a random length and there's a random number of rows
                for rownum in range(random.randint(0, 20))
            ]
            name = u"".join(random.choice(string.ascii_uppercase) for _ in range(10))
            yield name, self.data_point_type(lists=lsts)


class FloatListTypeWriterTest(GroupedCorpusWriterTest, unittest.TestCase):
    data_point_type = FloatListDocumentType()

    def get_documents(self):
        for i in range(15):
            # Generate a random table for this document
            # Each doc has a random length
            lst = [random.uniform(0., 10.) for i in range(random.randint(0, 20))]
            name = u"".join(random.choice(string.ascii_uppercase) for _ in range(10))
            yield name, self.data_point_type(list=lst)
