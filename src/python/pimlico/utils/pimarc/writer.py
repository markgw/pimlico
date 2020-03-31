import json
import os

from future.utils import raise_from

from pimlico.utils.pimarc.index import PimarcIndexAppender
from pimlico.utils.varint import encode
from .index import PimarcIndex


class PimarcWriter(object):
    """
    The Pimlico Archive format: writing new archives or appending existing ones.

    """
    def __init__(self, archive_filename, mode="w"):
        self.archive_filename = archive_filename
        self.index_filename = "{}i".format(archive_filename)
        self.append = mode == "a"

        if self.append:
            # Check the old archive already exists
            if not os.path.exists(archive_filename):
                raise IOError("cannot append to non-existent archive: {}".format(archive_filename))
            if not os.path.exists(self.index_filename):
                raise IOError("cannot append to archive: index file doesn't exist: {}".format(self.index_filename))
        else:
            # Remove any existing files
            if os.path.exists(archive_filename):
                os.remove(archive_filename)
            if os.path.exists(self.index_filename):
                os.remove(self.index_filename)

        self.archive_file = open(self.archive_filename, mode="ab" if self.append else "wb")
        self.index = PimarcIndexAppender(self.index_filename, mode="a" if self.append else "w")

    def close(self):
        self.archive_file.close()
        self.index.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write_file(self, data, name=None, metadata=None):
        """
        Append a write to the end of the archive. The metadata should be a dictionary
        that can be encoded as JSON (which is how it will be stored). The data should
        be a bytes object.

        If you want to write text files, you should encode the text as UTF-8 to get a
        bytes object and write that.

        Setting `name=X` is simply a shorthand for setting `metadata["name"]=X`.
        Either `name` or a metadata dict including the `name` key is required.

        """
        if metadata is None:
            metadata = {}

        if name is not None:
            filename = name
            metadata["name"] = name
        else:
            # The file's name should always be in the metadata as "name"
            try:
                filename = metadata["name"]
            except KeyError:
                raise MetadataError("metadata should include 'name' key")
        # Check where we're up to in the file
        # This tells us where the metadata starts, which will be stored in the index
        metadata_start = self.archive_file.tell()
        # Encode the metadata as utf-8 JSON
        try:
            metadata_data = json.dumps(metadata).encode("utf-8")
        except Exception as e:
            raise_from(MetadataError("problem encoding metadata as JSON"), e)

        # Write it to the file, including its length
        _write_var_length_data(self.archive_file, metadata_data)

        # Check where we're up to in the file
        # This tells us where the file data starts, which will be stored in the index
        data_start = self.archive_file.tell()
        # Write out the data, including its length
        _write_var_length_data(self.archive_file, data)

        # Add the file to the index
        self.index.append(filename, metadata_start, data_start)

    def flush(self):
        """
        Flush the archive's data out to disk, archive and index.

        """
        # First call flush(), which does a basic flush to RAM cache
        self.archive_file.flush()
        # Then we also need to force the system to write it to disk
        os.fsync(self.archive_file.fileno())
        # The index flush does the same with its file
        self.index.flush()


def _write_var_length_data(writer, data):
    """
    Write some data to a file-like object by first writing a varint that says how many
    bytes are in the data and then writing the data immediately following.

    """
    # Store the length of the data in bytes
    data_length = len(data)
    writer.write(encode(data_length))
    # Write the data as a bytes array
    return writer.write(data)


class MetadataError(Exception):
    pass
