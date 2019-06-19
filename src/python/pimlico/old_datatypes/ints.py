# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import struct
from cStringIO import StringIO

from pimlico.old_datatypes.documents import RawDocumentType
from pimlico.old_datatypes.table import get_struct
from pimlico.old_datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid


class IntegerListsDocumentType(RawDocumentType):
    def __init__(self, options, metadata):
        super(IntegerListsDocumentType, self).__init__(options, metadata)
        self._unpacker = None
        self.length_unpacker = get_struct(2, False, 1)
        self.length_size = self.length_unpacker.size
        self._int_size = None

    @property
    def unpacker(self):
        # Only ready when we've got metadata (data_ready() == True)
        if self._unpacker is None:
            # Read the metadata to prepare the reader struct
            bytes, signed = struct.unpack("B?", self.metadata["struct_format"])
            # Compile a struct for unpacking individual ints quickly
            self._unpacker = get_struct(bytes, signed, 1)
            self._int_size = self._unpacker.size
        return self._unpacker

    def process_document(self, data):
        reader = StringIO(data)
        return list(self.read_rows(reader))

    def read_rows(self, reader):
        unpacker = self.unpacker
        int_size = self._int_size

        def _read_row(length):
            for i in range(length):
                num_string = reader.read(int_size)
                try:
                    yield unpacker.unpack(num_string)[0]
                except struct.error as e:
                    if num_string == "":
                        raise IOError("file ended mid-row")
                    raise IOError("error interpreting int data: %s" % e)

        while True:
            # First read an int that tells us how long the row is
            row_length_string = reader.read(self.length_size)
            if row_length_string == "":
                # Reached end of file
                break
            row_length = self.length_unpacker.unpack(row_length_string)[0]
            # Read the whole row, one int at a time
            yield list(_read_row(row_length))


class IntegerListsDocumentCorpus(TarredCorpus):
    """
    Corpus of integer list data: each doc contains lists of ints. Unlike
    :class:`~pimlico.datatypes.table.IntegerTableDocumentCorpus`, they are not all constrained to have the same
    length. The downside is that the storage format (and probably I/O speed) isn't quite as good.
    It's still better than just storing ints as strings or JSON objects.

    By default, the ints are stored as C longs, which use 4 bytes. If you know you don't need ints this
    big, you can choose 1 or 2 bytes, or even 8 (long long). By default, the ints are unsigned, but they
    may be signed.

    """
    datatype_name = "integer_lists_corpus"
    data_point_type = IntegerListsDocumentType


class IntegerListsDocumentCorpusWriter(TarredCorpusWriter):
    def __init__(self, base_dir, signed=False, bytes=8, **kwargs):
        # Tell TarredCorpus not to encode/decode text data
        kwargs["encoding"] = None
        super(IntegerListsDocumentCorpusWriter, self).__init__(base_dir, **kwargs)
        self.signed = signed
        self.bytes = bytes

        # Prepare a struct for efficiently encoding int rows as bytes
        self.num_struct = get_struct(bytes, signed, 1)
        # Prepare another for encoding the row lengths
        self.length_struct = get_struct(2, False, 1)
        # Write the metadata to denote the representation format
        self.metadata["struct_format"] = struct.pack("B?", bytes, signed)

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        raw_data = StringIO()
        for row in doc:
            # Should be rows of ints
            try:
                raw_data.write(self.length_struct.pack(len(row)))
                for num in row:
                    raw_data.write(self.num_struct.pack(num))
            except struct.error as e:
                raise ValueError("error encoding int row %s using struct format %s: %s" %
                                 (row, self.num_struct.format, e))
        return raw_data.getvalue()


class IntegerListDocumentType(RawDocumentType):
    """
    Like IntegerListsDocumentType, but each document is treated as a single list of integers.

    """
    def __init__(self, options, metadata):
        super(IntegerListDocumentType, self).__init__(options, metadata)
        self._unpacker = None

    @property
    def unpacker(self):
        # Only ready when we've got metadata (data_ready() == True)
        if self._unpacker is None:
            # Read the metadata to prepare the reader struct
            bytes, signed = struct.unpack("B?", self.metadata["struct_format"])
            # Compile a struct for unpacking individual ints quickly
            self._unpacker = get_struct(bytes, signed, 1)
        return self._unpacker

    @property
    def int_size(self):
        return self.unpacker.size

    def process_document(self, data):
        reader = StringIO(data)
        return list(self.read_ints(reader))

    def read_ints(self, reader):
        while True:
            # Read the whole document, one int at a time
            num_string = reader.read(self.int_size)
            if num_string == "":
                return
            try:
                num = self.unpacker.unpack(num_string)[0]
            except struct.error as e:
                raise IOError("error interpreting int data: %s" % e)
            yield num


class IntegerListDocumentCorpus(TarredCorpus):
    """
    Corpus of integer data: each doc contains a single sequence of ints.

    By default, the ints are stored as C longs, which use 4 bytes. If you know you don't need ints this
    big, you can choose 1 or 2 bytes, or even 8 (long long). By default, the ints are unsigned, but they
    may be signed.

    """
    datatype_name = "integer_list_corpus"
    data_point_type = IntegerListDocumentType


class IntegerListDocumentCorpusWriter(TarredCorpusWriter):
    def __init__(self, base_dir, signed=False, bytes=8, **kwargs):
        # Tell TarredCorpus not to encode/decode text data
        kwargs["encoding"] = None
        super(IntegerListDocumentCorpusWriter, self).__init__(base_dir, **kwargs)
        self.signed = signed
        self.bytes = bytes

        # Prepare a struct for efficiently encoding int rows as bytes
        self.num_struct = get_struct(bytes, signed, 1)
        # Write the metadata to denote the representation format
        self.metadata["struct_format"] = struct.pack("B?", bytes, signed)

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        raw_data = StringIO()
        # Doc should be a list of ints
        for num in doc:
            try:
                raw_data.write(self.num_struct.pack(num))
            except struct.error as e:
                raise ValueError("error encoding int data %s using struct format %s: %s" %
                                 (num, self.num_struct.format, e))
        return raw_data.getvalue()
