import struct
from StringIO import StringIO

from pimlico.datatypes.documents import RawDocumentType
from pimlico.datatypes.table import get_struct
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter, pass_up_invalid


class IntegerListsDocumentType(RawDocumentType):
    def __init__(self, options, metadata):
        super(IntegerListsDocumentType, self).__init__(options, metadata)
        self._unpacker = None
        self.length_unpacker = get_struct(2, False, 1)
        self.length_size = self.length_unpacker.size

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
                num_string = reader.read(self.int_size)
                if num_string == "":
                    raise IOError("file ended mid-row")
                try:
                    num = self.unpacker.unpack(num_string)[0]
                except struct.error, e:
                    raise IOError("error interpreting int data: %s" % e)
                row.append(num)
            yield row


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
            except struct.error, e:
                raise ValueError("error encoding int row %s using struct format %s: %s" %
                                 (row, self.num_struct.format, e))
        return raw_data.getvalue()
