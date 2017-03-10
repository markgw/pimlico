"""
Similar to :mod:pimlico.datatypes.ints, but for lists of floats.

"""

import struct
from StringIO import StringIO

from pimlico.cli.browser.formatter import DocumentBrowserFormatter
from pimlico.datatypes.documents import RawDocumentType
from pimlico.datatypes.table import get_struct
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid


class FloatListsDocumentType(RawDocumentType):
    formatters = [("float_lists", "pimlico.datatypes.floats.FloatListsFormatter")]

    def __init__(self, options, metadata):
        super(FloatListsDocumentType, self).__init__(options, metadata)
        # Struct for reading in individual floats (actually doubles)
        self.unpacker = struct.Struct("<d")
        self.value_size = self.unpacker.size
        # Struct for unpacking the row length at the start of each row
        self.length_unpacker = get_struct(2, False, 1)
        self.length_size = self.length_unpacker.size

    def process_document(self, data):
        reader = StringIO(data)
        return list(self.read_rows(reader))

    def read_rows(self, reader):
        while True:
            # First read an int that tells us how long the row is
            row_length_string = reader.read(self.length_size)
            if row_length_string == "":
                # Reached end of file
                break
            row_length = self.length_unpacker.unpack(row_length_string)[0]

            # Read the whole row, one int at a time
            row = []
            for i in range(row_length):
                num_string = reader.read(self.value_size)
                if num_string == "":
                    raise IOError("file ended mid-row")
                try:
                    num = self.unpacker.unpack(num_string)[0]
                except struct.error, e:
                    raise IOError("error interpreting float data: %s" % e)
                row.append(num)
            yield row


class FloatListsFormatter(DocumentBrowserFormatter):
    DATATYPE = FloatListsDocumentType

    def format_document(self, doc):
        return "\n".join(
            " ".join("%.4f" % f for f in lst) for lst in doc
        )


class FloatListsDocumentCorpus(TarredCorpus):
    """
    Corpus of float list data: each doc contains lists of float. Unlike
    :class:`~pimlico.datatypes.table.IntegerTableDocumentCorpus`, they are not all constrained to have the same
    length. The downside is that the storage format (and probably I/O speed) isn't quite as efficient.
    It's still better than just storing ints as strings or JSON objects.

    The floats are stored as C double, which use 8 bytes. At the moment, we don't provide any way to change this.
    An alternative would be to use C floats, losing precision but (almost) halving storage size.

    """
    datatype_name = "float_lists_corpus"
    data_point_type = FloatListsDocumentType


class FloatListsDocumentCorpusWriter(TarredCorpusWriter):
    def __init__(self, base_dir, **kwargs):
        # Tell TarredCorpus not to encode/decode text data
        kwargs["encoding"] = None
        super(FloatListsDocumentCorpusWriter, self).__init__(base_dir, **kwargs)

        # Struct for writing individual floats (actually doubles)
        self.packer = struct.Struct("<d")
        # Prepare another for encoding the row lengths (ints)
        self.length_struct = get_struct(2, False, 1)

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        raw_data = StringIO()
        for row in doc:
            # Should be rows of floats
            try:
                raw_data.write(self.length_struct.pack(len(row)))
                for num in row:
                    raw_data.write(self.packer.pack(num))
            except struct.error, e:
                raise ValueError("error encoding float row %s using struct format %s: %s" %
                                 (row, self.packer.format, e))
        return raw_data.getvalue()


class FloatListDocumentType(RawDocumentType):
    """
    Like FloatListsDocumentType, but each document is treated as a single list of floats.

    """
    def __init__(self, options, metadata):
        super(FloatListDocumentType, self).__init__(options, metadata)
        # Struct for reading in individual floats (actually doubles)
        self.unpacker = struct.Struct("<d")
        self.value_size = self.unpacker.size

    def process_document(self, data):
        reader = StringIO(data)
        return list(self.read_floats(reader))

    def read_floats(self, reader):
        while True:
            # Read the whole document, one float at a time
            num_string = reader.read(self.value_size)
            if num_string == "":
                return
            try:
                num = self.unpacker.unpack(num_string)[0]
            except struct.error, e:
                raise IOError("error interpreting float data: %s" % e)
            yield num


class FloatListDocumentCorpus(TarredCorpus):
    """
    Corpus of float data: each doc contains a single sequence of floats.

    The floats are stored as C doubles, using 8 bytes each.

    """
    datatype_name = "float_list_corpus"
    data_point_type = FloatListDocumentType


class FloatListDocumentCorpusWriter(TarredCorpusWriter):
    def __init__(self, base_dir, **kwargs):
        # Tell TarredCorpus not to encode/decode text data
        kwargs["encoding"] = None
        super(FloatListDocumentCorpusWriter, self).__init__(base_dir, **kwargs)

        # Struct for writing individual floats (actually doubles)
        self.packer = struct.Struct("<d")

    @pass_up_invalid
    def document_to_raw_data(self, doc):
        raw_data = StringIO()
        # Doc should be a list of ints
        for num in doc:
            try:
                raw_data.write(self.packer.pack(num))
            except struct.error, e:
                raise ValueError("error encoding float data %s using struct format %s: %s" %
                                 (num, self.packer.format, e))
        return raw_data.getvalue()
