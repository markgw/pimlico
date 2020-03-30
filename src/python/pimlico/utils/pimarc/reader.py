import json

from .index import PimarcIndex
from pimlico.utils.varint import decode_stream


class PimarcReader(object):
    """
    The Pimlico Archive format: read-only archive.

    """
    def __init__(self, archive_filename):
        self.archive_filename = archive_filename
        self.index_filename = "{}i".format(archive_filename)
        self.index = None
        self.archive_file = None

    def open(self):
        """
        Open the archive file.

        """
        return open(self.archive_filename, mode="rb")

    def __enter__(self):
        self.archive_file = self.open()
        self.index = PimarcIndex.load(self.index_filename)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.archive_file.close()

    def __getitem__(self, item):
        """
        Random access into the archive. Load a named file's data and metadata.

        """
        # Look up the filename in the index and get pointers to its metadata and data
        metadata_start, data_start = self.index[item]
        # Jump to the start of the metadata
        self.archive_file.seek(metadata_start)
        # Read the metadata
        metadata = self._read_metadata()
        # There's some redundancy in this case: we're now presumably at the start
        # of the data, so don't need data_start
        # Assume that this is the case and continue reading from where we stopped
        data = _read_var_length_data(self.archive_file)
        return metadata, data

    def _read_metadata(self):
        """
        Assuming the file is currently at the start of a metadata block, read and
        parse that metadata.

        """
        # Read the metadata
        metadata_data = _read_var_length_data(self.archive_file)
        # Decode the metadata and parse as JSON
        metadata = json.loads(metadata_data.decode("utf-8"))
        return metadata

    def iter_metadata(self):
        """
        Iterate over all files in the archive, yielding just the metadata, skipping
        over the data.

        """
        # Make sure we're at the start of the file
        self.archive_file.seek(0)
        while True:
            # Try reading the metadata of the next file
            try:
                metadata = self._read_metadata()
            except EOFError:
                # At this point, it's normal to get an EOF: we've just got to the end neatly
                break
            # This should be followed by the file's data, which we skip over, since we don't need it
            _skip_var_length_data(self.archive_file)
            yield metadata

    def iter_files(self):
        """
        Iterate over files, together with their JSON metadata, which includes their name (as "name").

        """
        # Make sure we're at the start of the file
        self.archive_file.seek(0)
        while True:
            # Try reading the metadata of the next file
            try:
                metadata = self._read_metadata()
            except EOFError:
                # At this point, it's normal to get an EOF: we've just got to the end neatly
                break
            # This should be followed by the file's data immediately
            # Read it in
            # If there's an EOF here, something's wrong with the file
            data = _read_var_length_data(self.archive_file)
            yield metadata, data

    def __iter__(self):
        return self.iter_files()

    def __len__(self):
        return len(self.index)


def _read_var_length_data(reader):
    """
    Read some data from a file-like object by first reading a varint that says how many
    bytes are in the data and then reading the data immediately following.

    """
    # Get a single varint from the reader stream
    data_length = decode_stream(reader)
    # Read the data as a bytes array
    return reader.read(data_length)


def _skip_var_length_data(reader):
    """
    Like read_var_length_data, but doesn't actually read the data. Just reads the length
    indicator and seeks to the end of the data.

    """
    data_length = decode_stream(reader)
    reader.seek(data_length, 1)
