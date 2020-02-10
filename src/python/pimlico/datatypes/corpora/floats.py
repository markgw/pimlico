# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Corpora consisting of lists of ints. These data point types are useful,
for example, for encoding text or other sequence data as integer IDs.
They are designed to be fast to read.

"""
from __future__ import absolute_import

from future import standard_library

standard_library.install_aliases()
from builtins import range
from builtins import object

import struct
from io import BytesIO

from pimlico.cli.browser.tools.formatter import DocumentBrowserFormatter
from pimlico.datatypes.corpora.data_points import RawDocumentType
from .table import get_struct


class FloatListsDocumentType(RawDocumentType):
    """
    Corpus of float list data: each doc contains lists of float. Unlike
    :class:`~pimlico.datatypes.table.IntegerTableDocumentCorpus`, they are not all constrained to have the same
    length. The downside is that the storage format (and probably I/O speed) isn't quite as efficient.
    It's still better than just storing ints as strings or JSON objects.

    The floats are stored as C double, which use 8 bytes. At the moment, we don't provide any way to change this.
    An alternative would be to use C floats, losing precision but (almost) halving storage size.

    """
    metadata_defaults = dict(RawDocumentType.metadata_defaults, **{
        "bytes": (
            8,
            "Number of bytes to use to represent each int. Default: 8",
        ),
        "signed": (
            False,
            "Stored signed integers. Default: False",
        ),
    })

    def reader_init(self, reader):
        super(FloatListsDocumentType, self).reader_init(reader)
        # Struct for reading in individual floats (actually doubles)
        self.struct = struct.Struct("<d")
        self.value_size = self.struct.size
        # Struct for unpacking the row length at the start of each row
        self.length_struct = get_struct(2, False, 1)
        self.length_size = self.length_struct.size

    def writer_init(self, writer):
        super(FloatListsDocumentType, self).writer_init(writer)
        # Struct for reading in individual floats (actually doubles)
        self.struct = struct.Struct("<d")
        self.value_size = self.struct.size
        # Struct for unpacking the row length at the start of each row
        self.length_struct = get_struct(2, False, 1)
        self.length_size = self.length_struct.size

    class Document(object):
        keys = ["lists"]

        def raw_to_internal(self, raw_data):
            reader = BytesIO(raw_data)
            lists = list(self.read_rows(reader))
            return {
                "lists": lists,
            }

        @property
        def lists(self):
            return self.internal_data["lists"]

        def read_rows(self, reader):
            while True:
                # First read an int that tells us how long the row is
                row_length_string = reader.read(self.data_point_type.length_size)
                if len(row_length_string) == 0:
                    # Reached end of file
                    break
                row_length = self.data_point_type.length_struct.unpack(row_length_string)[0]

                # Read the whole row, one int at a time
                row = []
                for i in range(row_length):
                    num_string = reader.read(self.data_point_type.value_size)
                    if num_string == "":
                        raise IOError("file ended mid-row")
                    try:
                        num = self.data_point_type.struct.unpack(num_string)[0]
                    except struct.error as e:
                        raise IOError("error interpreting float data: %s" % e)
                    row.append(num)
                yield row

        def internal_to_raw(self, internal_data):
            raw_data = BytesIO()
            for row in internal_data["lists"]:
                # Should be rows of floats
                try:
                    raw_data.write(bytes(self.data_point_type.length_struct.pack(len(row))))
                    for num in row:
                        raw_data.write(bytes(self.data_point_type.struct.pack(num)))
                except struct.error as e:
                    raise ValueError("error encoding float row %s using struct format %s: %s" %
                                     (row, self.data_point_type.struct.format, e))
            return raw_data.getvalue()


class FloatListDocumentType(RawDocumentType):
    """
    Corpus of float data: each doc contains a single sequence of floats.

    The floats are stored as C doubles, using 8 bytes each.

    """
    def reader_init(self, reader):
        super(FloatListDocumentType, self).reader_init(reader)
        # Struct for reading in individual floats (actually doubles)
        self.struct = struct.Struct("<d")
        self.value_size = self.struct.size

    def writer_init(self, writer):
        super(FloatListDocumentType, self).writer_init(writer)
        # Struct for reading in individual floats (actually doubles)
        self.struct = struct.Struct("<d")
        self.value_size = self.struct.size

    class Document(object):
        keys = ["list"]

        def raw_to_internal(self, raw_data):
            reader = BytesIO(raw_data)
            lst = list(self.read_rows(reader))
            return {
                "list": lst,
            }

        @property
        def list(self):
            return self.internal_data["list"]

        def read_rows(self, reader):
            while True:
                # Read the whole document, one float at a time
                num_string = reader.read(self.data_point_type.value_size)
                if len(num_string) == 0:
                    return
                try:
                    num = self.data_point_type.struct.unpack(num_string)[0]
                except struct.error as e:
                    raise IOError("error interpreting float data: %s" % e)
                yield num

        def internal_to_raw(self, internal_data):
            raw_data = BytesIO()
            # Doc should be a list of ints
            for num in internal_data["list"]:
                try:
                    raw_data.write(bytes(self.data_point_type.struct.pack(num)))
                except struct.error as e:
                    raise ValueError("error encoding float data %s using struct format %s: %s" %
                                     (num, self.data_point_type.struct.format, e))
            return raw_data.getvalue()


class FloatListsFormatter(DocumentBrowserFormatter):
    DATATYPE = FloatListsDocumentType

    def format_document(self, doc):
        return "\n".join(
            " ".join("%.4f" % f for f in lst) for lst in doc.lists
        )


class VectorDocumentType(RawDocumentType):
    """
    Like FloatListDocumentType, but each document has the same number of float values.

    Each document contains a single list of floats
    and each one has the same length. That is, each document is one vector.

    The floats are stored as C doubles, using 8 bytes each.

    """
    formatters = [("vector", "pimlico.datatypes.floats.VectorFormatter")]
    metadata_defaults = {"dimensions": (10, "Number of dimensions in each vector (default: 10)")}

    def reader_init(self, reader):
        super(VectorDocumentType, self).reader_init(reader)
        # Prepare struct for reading in the whole vector
        dim = reader.metadata["dimensions"]
        self.struct = struct.Struct("<" + "d"*dim)
        self.value_size = self.struct.size

    def writer_init(self, writer):
        super(VectorDocumentType, self).writer_init(writer)
        # Prepare struct for writing out the whole vector
        dim = writer.metadata["dimensions"]
        self.struct = struct.Struct("<" + "d"*dim)
        self.value_size = self.struct.size

    class Document(object):
        keys = ["vector"]

        def raw_to_internal(self, raw_data):
            try:
                return {"vector": self.data_point_type.struct.unpack(raw_data),}
            except struct.error as e:
                raise IOError("error interpreting float vector data: %s" % e)

        def internal_to_raw(self, internal_data):
            try:
                return self.data_point_type.struct.pack(internal_data["vector"])
            except struct.error as e:
                raise ValueError("error encoding float data using struct format %s: %s" %
                                 (self.data_point_type.struct.format, e))


class VectorFormatter(DocumentBrowserFormatter):
    DATATYPE = VectorDocumentType

    def format_document(self, doc):
        return "\n".join("{:.3f}".format(f) for f in doc.vector)
