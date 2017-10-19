# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import struct
from StringIO import StringIO

from pimlico.datatypes.documents import RawDocumentType
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid

BYTE_FORMATS = {
    # (num bytes, signed)
    (1, True): "b",   # signed char
    (1, False): "B",  # unsigned char
    (2, True): "h",   # signed short
    (2, False): "H",  # unsigned short
    (4, True): "l",   # signed long
    (4, False): "L",  # unsigned long
    (8, True): "q",   # signed long long
    (8, False): "Q",  # unsigned long long
}


def get_struct(bytes, signed, row_length):
    # Put together the formatting string for converting ints to bytes
    if (bytes, signed) not in BYTE_FORMATS:
        raise ValueError("invalid specification for int format: signed=%s, bytes=%s. signed must be bool, "
                         "bytes in [1, 2, 4, 8]" % (signed, bytes))
    format_string = "<" + BYTE_FORMATS[(bytes, signed)] * row_length
    # Compile the format for faster encoding
    return struct.Struct(format_string)


class IntegerTableDocumentType(RawDocumentType):
    def __init__(self, options, metadata):
        super(IntegerTableDocumentType, self).__init__(options, metadata)
        self._unpacker = None

    @property
    def unpacker(self):
        # Only ready when we've got metadata (data_ready() == True)
        if self._unpacker is None:
            # Read the metadata to prepare the reader struct
            bytes, signed, row_length = struct.unpack("B?H", self.metadata["struct_format"])
            # Compile a struct for unpacking these quickly
            self._unpacker = get_struct(bytes, signed, row_length)
        return self._unpacker

    @property
    def row_size(self):
        return self.unpacker.size

    def process_document(self, data):
        reader = StringIO(data)
        return list(self.read_rows(reader))

    def read_rows(self, reader):
        while True:
            # Read data for a single row
            row_string = reader.read(self.row_size)
            if row_string == "":
                # Reach end of file
                break
            try:
                row = self.unpacker.unpack(row_string)
            except struct.error, e:
                if len(row_string) < self.row_size:
                    # Got a partial row at end of file
                    raise IOError("found partial row at end of file: last row has byte length %d, not %d" %
                                  (len(row_string), self.row_size))
                else:
                    raise IOError("error interpreting row: %s" % e)
            yield row


class IntegerTableDocumentCorpus(TarredCorpus):
    """
    Corpus of tabular integer data: each doc contains rows of ints, where each row contains the same number
    of values. This allows a more compact representation, which doesn't require converting the ints to strings or
    scanning for line ends, so is quite a bit quicker and results in much smaller file sizes. The downside is that
    the files are not human-readable.

    By default, the ints are stored as C longs, which use 4 bytes. If you know you don't need ints this
    big, you can choose 1 or 2 bytes, or even 8 (long long). By default, the ints are unsigned, but they
    may be signed.

    """
    datatype_name = "integer_table_corpus"
    data_point_type = IntegerTableDocumentType


class IntegerTableDocumentCorpusWriter(TarredCorpusWriter):
    def __init__(self, base_dir, row_length, signed=False, bytes=8, **kwargs):
        # Tell TarredCorpus not to encode/decode text data
        kwargs["encoding"] = None
        super(IntegerTableDocumentCorpusWriter, self).__init__(base_dir, **kwargs)
        self.row_length = row_length
        self.signed = signed
        self.bytes = bytes

        # Prepare a struct for efficiently encoding int rows as bytes
        self.struct = get_struct(bytes, signed, row_length)
        # Write the metadata to denote the representation format
        self.metadata["struct_format"] = struct.pack("B?H", bytes, signed, row_length)

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        raw_data = StringIO()
        for row in doc:
            # Should be rows of ints of the correct length
            try:
                raw_data.write(self.struct.pack(*row))
            except struct.error, e:
                # Instead of checking the rows before encoding, catch any encoding errors and give helpful messages
                if len(row) != self.row_length:
                    raise ValueError("tried to write a row of length %d to a table writer with row length %d" %
                                     (len(row), self.row_length))
                else:
                    raise ValueError("error encoding int row %s using struct format %s: %s" %
                                     (row, self.struct.format, e))
        return raw_data.getvalue()
