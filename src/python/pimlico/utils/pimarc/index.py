import json
import os
from collections import OrderedDict
from builtins import *

from .utils import _read_var_length_data, _skip_var_length_data


class PimarcIndex(object):
    """
    Simple index to accompany a Pimarc, stored along with the `.prc` file as a
    `.prci` file. Provides a list of the filenames in the archive, along with
    the starting byte of the file's metadata and data.

    filenames is an OrderedDict mapping filename -> (metadata start byte, data start byte).

    """
    def __init__(self):
        self.filenames = OrderedDict()

    def get_metadata_start_byte(self, filename):
        try:
            return self.filenames[filename][0]
        except KeyError:
            raise FilenameNotInArchive(filename)

    def get_data_start_byte(self, filename):
        try:
            return self.filenames[filename][1]
        except KeyError:
            raise FilenameNotInArchive(filename)

    def __getitem__(self, item):
        """ Returns a pair containing the metadata start byte and the data start byte. """
        return self.filenames[item]

    def __iter__(self):
        """ Simply iterate over the filenames. You can access the data using these as args to other methods. """
        return iter(self.filenames)

    def __len__(self):
        return len(self.filenames)

    def __contains__(self, item):
        return item in self.filenames

    def keys(self):
        return self.filenames.keys()

    def append(self, filename, metadata_start, data_start):
        if filename in self.filenames:
            raise DuplicateFilename(filename)
        self.filenames[filename] = (metadata_start, data_start)

    @staticmethod
    def load(filename):
        index = PimarcIndex()
        with open(filename, "r") as f:
            for line in f:
                # Remove the newline char
                line = line[:-1]
                # There should be three tab-separated values: filename, metadata start and data start
                doc_filename, metadata_start, data_start = line.split("\t")
                metadata_start, data_start = int(metadata_start), int(data_start)
                index.append(doc_filename, metadata_start, data_start)
        return index

    def save(self, path):
        with open(path, "w") as f:
            for doc_filename, (metadata_start, data_start) in self.filenames.items():
                f.write("{}\t{}\t{}\n".format(doc_filename, metadata_start, data_start))


class PimarcIndexAppender(object):
    """
    Class for writing out a Pimarc index as each file is added to the archive.
    This is used by the Pimarc writer, instead of creating a PimarcIndex and
    calling `save()`, so that the index is always kept up to date with what's
    in the archive.

    Mode may be `"w"` to write a new index or `"a"` to append to an existing
    one.

    """
    def __init__(self, store_path, mode="w"):
        self.store_path = store_path
        self.filenames = OrderedDict()
        self.mode = mode

        if self.mode == "a":
            # Load the existing index so we can append
            self._load()
            self.fileobj = open(self.store_path, "a")
        else:
            # Start a new index
            self.fileobj = open(self.store_path, "w")

    def __len__(self):
        return len(self.filenames)

    def __contains__(self, item):
        return item in self.filenames

    def append(self, filename, metadata_start, data_start):
        if filename in self.filenames:
            raise DuplicateFilename(filename)
        self.filenames[filename] = (metadata_start, data_start)
        # Add a line to the end of the index
        self.fileobj.write("{}\t{}\t{}\n".format(filename, metadata_start, data_start))

    def close(self):
        self.fileobj.close()

    def _load(self):
        with open(self.store_path, "r") as f:
            for line in f:
                # Remove the newline char
                line = line[:-1]
                # There should be three tab-separated values: filename, metadata start and data start
                doc_filename, metadata_start, data_start = line.split("\t")
                metadata_start, data_start = int(metadata_start), int(data_start)
                self.filenames[doc_filename] = (metadata_start, data_start)

    def flush(self):
        # First call flush(), which does a basic flush to RAM cache
        self.fileobj.flush()
        # Then we also need to force the system to write it to disk
        os.fsync(self.fileobj.fileno())


def reindex(pimarc_path):
    """
    Rebuild the index of a Pimarc archive from its data file (.prc).

    Stores the new index in the correct location (.prci), overwriting any existing index.

    :param pimarc_path: path to the .prc file
    :return: the PimarcIndex
    """
    if not pimarc_path.endswith(".prc"):
        raise IndexWriteError("input pimarc path does not have the correct extension (.prc)")
    index_path = "{}i".format(pimarc_path)

    # Create an empty index
    index = PimarcIndex()
    # Read in each file in turn, reading the metadata to get the name and skipping the file content
    with open(pimarc_path, "rb") as data_file:
        try:
            while True:
                # Check where the metadata starts
                metadata_start_byte = data_file.tell()
                # First read the file's metadata block
                metadata = json.loads(_read_var_length_data(data_file).decode("utf-8"))
                # From that we can get the name
                filename = metadata["name"]
                # Now we're at the start of the file data
                data_start_byte = data_file.tell()
                # Skip over the data: we don't need to read that
                _skip_var_length_data(data_file)
                # Now add the entry to the index, with pointers to the start bytes
                index.append(filename, metadata_start_byte, data_start_byte)
        except EOFError:
            # Reached the end of the file
            pass

    index.save(index_path)
    return index


class FilenameNotInArchive(Exception):
    def __init__(self, filename):
        super().__init__(u"filename '{}' not found in archive".format(filename))
        self.filename = filename


class DuplicateFilename(Exception):
    def __init__(self, filename):
        super().__init__(u"filename '{}' already in archive: cannot add it again".format(filename))
        self.filename = filename


class IndexWriteError(Exception):
    pass
