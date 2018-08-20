# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Corpora where each document is a table, i.e. a list of lists, where each
row has the same length and each column has a single datatype.
This is designed to be fast to read, but is not a very flexible datatype.

"""

import struct
from StringIO import StringIO

from pimlico.datatypes.corpora.data_points import RawDocumentType
from pimlico.utils.core import cached_property

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
    """
    Corpus of tabular integer data: each doc contains rows of ints, where each row contains the same number
    of values. This allows a more compact representation, which doesn't require converting the ints to strings or
    scanning for line ends, so is quite a bit quicker and results in much smaller file sizes. The downside is that
    the files are not human-readable.

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
        "row_length": (
            1,
            "Row length - number of integers in each row. Default: 1",
        ),
    })

    def reader_init(self, reader):
        super(IntegerTableDocumentType, self).reader_init(reader)
        self.bytes = self.metadata["bytes"]
        self.signed = self.metadata["signed"]
        self.row_length = self.metadata["row_length"]
        self.struct = get_struct(self.bytes, self.signed, self.row_length)

    def writer_init(self, writer):
        super(IntegerTableDocumentType, self).writer_init(writer)
        # Metadata should have been set by this point, using kwargs to override the defaults
        self.bytes = writer.metadata["bytes"]
        self.signed = writer.metadata["signed"]
        self.row_length = writer.metadata["row_length"]
        self.struct = get_struct(self.bytes, self.signed, self.row_length)

    class Document:
        keys = ["table"]

        def raw_to_internal(self, raw_data):
            reader = StringIO(raw_data)
            table = list(self.read_rows(reader))
            return {
                "table": table,
            }

        @property
        def table(self):
            return self.internal_data["table"]

        @cached_property
        def row_size(self):
            return self.data_point_type.struct.size

        def read_rows(self, reader):
            while True:
                # Read data for a single row
                row_string = reader.read(self.row_size)
                if row_string == "":
                    # Reach end of file
                    break
                try:
                    row = self.data_point_type.struct.unpack(row_string)
                except struct.error, e:
                    if len(row_string) < self.row_size:
                        # Got a partial row at end of file
                        raise IOError("found partial row at end of file: last row has byte length %d, not %d" %
                                      (len(row_string), self.row_size))
                    else:
                        raise IOError("error interpreting row: %s" % e)
                yield row

        def internal_to_raw(self, internal_data):
            raw_data = StringIO()
            for row in internal_data["table"]:
                # Should be rows of ints of the correct length
                try:
                    raw_data.write(self.data_point_type.struct.pack(*row))
                except struct.error, e:
                    # Instead of checking the rows before encoding, catch any encoding errors and give helpful messages
                    if len(row) != self.data_point_type.row_length:
                        raise ValueError("tried to write a row of length %d to a table writer with row length %d" %
                                         (len(row), self.data_point_type.row_length))
                    else:
                        raise ValueError("error encoding int row %s using struct format %s: %s" %
                                         (row, self.data_point_type.struct.format, e))
            return raw_data.getvalue()
