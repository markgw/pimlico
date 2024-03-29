# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

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
from builtins import bytes

import struct
from io import StringIO, BytesIO

from pimlico.datatypes.corpora.data_points import RawDocumentType
from pimlico.utils.core import cached_property
from .table import get_struct


class IntegerListsDocumentType(RawDocumentType):
    """
    Corpus of integer list data: each doc contains lists of ints. Unlike
    :class:`~pimlico.datatypes.table.IntegerTableDocumentType`, they are not all constrained to have the same
    length. The downside is that the storage format (and I/O speed) isn't quite as good.
    It's still better than just storing ints as strings or JSON objects.

    By default, the ints are stored as C longs, which use 4 bytes. If you know you don't need ints this
    big, you can choose 1 or 2 bytes, or even 8 (long long). By default, the ints are unsigned, but they
    may be signed.

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
        "row_length_bytes": (
            2,
            "Number of bytes to use to encode the length of each row. Default: 2. Increase if you "
            "need to store very long lists"
        ),
    })
    data_point_type_supports_python2 = True

    @property
    def bytes(self):
        return self.metadata.get("bytes", self.metadata_defaults["bytes"][0])

    @property
    def signed(self):
        return self.metadata.get("signed", self.metadata_defaults["signed"][0])

    @property
    def row_length_bytes(self):
        return self.metadata.get("row_length_bytes", self.metadata_defaults["row_length_bytes"][0])

    @property
    def int_size(self):
        return self.struct.size

    @property
    def length_size(self):
        return self.length_struct.size

    def writer_init(self, writer):
        super(IntegerListsDocumentType, self).writer_init(writer)
        # Metadata should have been set by this point, using kwargs to override the defaults
        self.metadata["bytes"] = writer.metadata["bytes"]
        self.metadata["signed"] = writer.metadata["signed"]
        self.metadata["row_length_bytes"] = writer.metadata["row_length_bytes"]

    @cached_property
    def struct(self):
        return get_struct(self.bytes, self.signed, 1)

    @cached_property
    def length_struct(self):
        # We use a separate struct for the row lengths
        return get_struct(self.row_length_bytes, False, 1)

    def __getstate__(self):
        # Don't pickle the prepared structs, as they don't pickle nicely
        # They get recreated on demand anyway
        state = dict(self.__dict__)
        if "struct" in state:
            del state["struct"]
        if "length_struct" in state:
            del state["length_struct"]
        return state

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
            unpacker = self.data_point_type.struct
            int_size = self.data_point_type.int_size
            length_unpacker = self.data_point_type.length_struct
            length_size = self.data_point_type.length_struct.size

            def _read_row(length):
                for i in range(length):
                    num_string = reader.read(int_size)
                    if num_string == b"":
                        raise IOError("file ended mid-row")
                    try:
                        yield unpacker.unpack(num_string)[0]
                    except struct.error as e:
                        raise IOError("error interpreting int data: %s" % e)

            while True:
                # First read an int that tells us how long the row is
                row_length_string = reader.read(length_size)
                if row_length_string == b"":
                    # Reached end of file
                    break
                row_length = length_unpacker.unpack(row_length_string)[0]
                # Read the whole row, one int at a time
                yield list(_read_row(row_length))

        def internal_to_raw(self, internal_data):
            raw_data = BytesIO()
            for row in internal_data["lists"]:
                # Should be rows of ints
                try:
                    raw_data.write(bytes(self.data_point_type.length_struct.pack(len(row))))
                    for num in row:
                        raw_data.write(bytes(self.data_point_type.struct.pack(num)))
                except struct.error as e:
                    raise ValueError("error encoding int row %s using struct format %s: %s" %
                                     (row, self.data_point_type.struct.format, e))
            return raw_data.getvalue()


class IntegerListDocumentType(RawDocumentType):
    """
    Corpus of integer data: each doc contains a single sequence of ints.

    Like IntegerListsDocumentType, but each document is treated as a single list of integers.

    By default, the ints are stored as C longs, which use 4 bytes. If you know you don't need ints this
    big, you can choose 1 or 2 bytes, or even 8 (long long). By default, the ints are unsigned, but they
    may be signed.

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
    data_point_type_supports_python2 = True

    def reader_init(self, reader):
        super(IntegerListDocumentType, self).reader_init(reader)
        self.bytes = self.metadata["bytes"]
        self.signed = self.metadata["signed"]
        self.int_size = self.struct.size

    def writer_init(self, writer):
        super(IntegerListDocumentType, self).writer_init(writer)
        # Metadata should have been set by this point, using kwargs to override the defaults
        self.bytes = writer.metadata["bytes"]
        self.signed = writer.metadata["signed"]

    @cached_property
    def struct(self):
        return get_struct(self.bytes, self.signed, 1)

    def __getstate__(self):
        # Don't pickle the prepared struct, as it doesn't pickle nicely
        # It gets recreated on demand anyway
        state = dict(self.__dict__)
        if "struct" in state:
            del state["struct"]
        return state

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
                # Read the whole document, one int at a time
                num_string = reader.read(self.data_point_type.int_size)
                if len(num_string) == 0:
                    return
                try:
                    num = self.data_point_type.struct.unpack(num_string)[0]
                except struct.error as e:
                    raise IOError("error interpreting int data: %s" % e)
                yield num

        def internal_to_raw(self, internal_data):
            raw_data = BytesIO()
            # Doc should be a list of ints
            for num in internal_data["list"]:
                try:
                    raw_data.write(self.data_point_type.struct.pack(num))
                except struct.error as e:
                    raise ValueError("error encoding int data %s using struct format %s: %s" %
                                     (num, self.data_point_type.struct.format, e))
            return raw_data.getvalue()


class IntegerDocumentType(RawDocumentType):
    """
    Corpus of integer data: each doc contains a single int.

    This may be useful, for example, for storing predicted or gold standard class labels
    for documents.

    By default, the ints are stored as C longs, which use 4 bytes. If you know you don't need ints this
    big, you can choose 1 or 2 bytes, or even 8 (long long). By default, the ints are unsigned, but they
    may be signed.

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
    data_point_type_supports_python2 = True

    def reader_init(self, reader):
        super(IntegerDocumentType, self).reader_init(reader)
        self.bytes = self.metadata["bytes"]
        self.signed = self.metadata["signed"]
        self.int_size = self.struct.size

    def writer_init(self, writer):
        super(IntegerDocumentType, self).writer_init(writer)
        # Metadata should have been set by this point, using kwargs to override the defaults
        self.bytes = writer.metadata["bytes"]
        self.signed = writer.metadata["signed"]

    @cached_property
    def struct(self):
        return get_struct(self.bytes, self.signed, 1)

    def __getstate__(self):
        # Don't pickle the prepared struct, as it doesn't pickle nicely
        # It gets recreated on demand anyway
        state = dict(self.__dict__)
        if "struct" in state:
            del state["struct"]
        return state

    class Document(object):
        keys = ["val"]

        def raw_to_internal(self, raw_data):
            # Read the whole document, which should be a single int
            if len(raw_data) != self.data_point_type.int_size:
                raise IOError("expected {} bytes in single-int doc, got {}".format(
                    self.data_point_type.int_size, len(raw_data)))
            try:
                val = self.data_point_type.struct.unpack(raw_data)[0]
            except struct.error as e:
                raise IOError("error interpreting int data: %s" % e)
            return {
                "val": val,
            }

        @property
        def list(self):
            return self.internal_data["val"]

        def internal_to_raw(self, internal_data):
            # Doc should be a single int
            val = internal_data["val"]
            try:
                return self.data_point_type.struct.pack(val)
            except struct.error as e:
                raise ValueError("error encoding int data %s using struct format %s: %s" %
                                 (val, self.data_point_type.struct.format, e))
