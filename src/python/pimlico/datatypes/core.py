# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Some basic core datatypes that are commonly used for simple datatypes, file types, etc.

.. versionadded::0.6

   Some core datatypes were moved here from :mod:`.base` to separate the base datatypes, which are typically
   not used themselves (i.e. more or less abstract), from the core datatypes, which are simply commonly
   used.

"""
import os

from pimlico.datatypes import PimlicoDatatype, PimlicoDatatypeWriter
from pimlico.datatypes.files import NamedFileCollection


class SingleTextDocument(NamedFileCollection):
    datatype_name = "single_doc"
    filenames = ["data.txt"]

    def read_data(self):
        with open(os.path.join(self.data_dir, "data.txt"), "r") as f:
            return f.read().decode("utf-8")


class SingleTextDocumentWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir, **kwargs):
        super(SingleTextDocumentWriter, self).__init__(base_dir, **kwargs)
        self.data = ""
        self.output_path = os.path.join(self.data_dir, "data.txt")

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(SingleTextDocumentWriter, self).__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            # Always encode data as utf-8
            data = self.data.encode("utf-8")
            # Write out the data file
            with open(self.output_path, "w") as f:
                f.write(data)


class Dict(NamedFileCollection):
    """
    Simply stores a Python dict, pickled to disk.

    """
    datatype_name = "dict"
    filenames = ["data"]

    @property
    def data(self):
        import cPickle as pickle
        with open(os.path.join(self.data_dir, "data"), "r") as f:
            return pickle.load(f)


class DictWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir, **kwargs):
        super(DictWriter, self).__init__(base_dir, **kwargs)
        self.data = {}
        self.output_path = os.path.join(self.data_dir, "data")

    def __exit__(self, exc_type, exc_val, exc_tb):
        import cPickle as pickle

        super(DictWriter, self).__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            # Write out the data file
            with open(self.output_path, "w") as f:
                pickle.dump(self.data, f, -1)


class StringList(PimlicoDatatype):
    """
    Simply stores a Python list of strings, written out to disk in a readable form. Not the most efficient
    format, but if the list isn't humungous it's OK (e.g. storing vocabularies).

    """
    datatype_name = "string_list"

    def data_ready(self):
        return self.path is not None and os.path.exists(self.path)

    @property
    def path(self):
        if "path" in self.options:
            return self.options["path"]
        elif not super(StringList, self).data_ready():
            return None
        else:
            return os.path.join(self.data_dir, "data")

    @property
    def data(self):
        with open(self.path, "r") as f:
            return f.read().decode("utf-8").splitlines()


class StringListWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir, **kwargs):
        super(StringListWriter, self).__init__(base_dir, **kwargs)
        self.data = []
        self.output_path = os.path.join(self.data_dir, "data")

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(StringListWriter, self).__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            # Write out the data file
            with open(self.output_path, "w") as f:
                f.write((u"\n".join(self.data)).encode("utf-8"))