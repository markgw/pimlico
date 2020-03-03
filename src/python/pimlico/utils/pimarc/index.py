from collections import OrderedDict
from builtins import *


class PimarcIndex(object):
    """
    Simple index to accompany a Pimarc, stored along with the `.prc` file as a
    `.prci` file. Provides a list of the filenames in the archive, along with
    the starting byte of the file's metadata and data.

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
        return self.get_metadata_start_byte(item), self.get_data_start_byte(item)

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


class FilenameNotInArchive(Exception):
    def __init__(self, filename):
        super().__init__(u"filename '{}' not found in archive".format(filename))
        self.filename = filename


class DuplicateFilename(Exception):
    def __init__(self, filename):
        super().__init__(u"filename '{}' already in archive: cannot add it again".format(filename))
        self.filename = filename
