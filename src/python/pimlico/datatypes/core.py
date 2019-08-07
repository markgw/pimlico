# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Some basic core datatypes that are commonly used for passing simple data, like
strings and dicts, through pipelines.

"""
from future import standard_library

standard_library.install_aliases()
from builtins import object

import io
import os

from pimlico.datatypes.base import PimlicoDatatype

__all__ = ["Dict", "StringList"]


class Dict(PimlicoDatatype):
    """
    Simply stores a Python dict, pickled to disk. All content in the dict should
    be pickleable.

    """
    datatype_name = "dict"

    class Reader(object):
        class Setup(object):
            def get_required_paths(self):
                return ["data"]

        def get_dict(self):
            import pickle as pickle
            with open(os.path.join(self.data_dir, "data"), "rb") as f:
                return pickle.load(f)

    class Writer(object):
        required_tasks = ["dict"]

        def write_dict(self, d):
            import pickle as pickle
            # Write out the data file
            with open(os.path.join(self.data_dir, "data"), "wb") as f:
                pickle.dump(d, f, -1)
            self.task_complete("dict")


class StringList(PimlicoDatatype):
    """
    Simply stores a Python list of strings, written out to disk in a readable form. Not the most efficient
    format, but if the list isn't humungous it's OK (e.g. storing vocabularies).

    """
    datatype_name = "string_list"

    class Reader(object):
        class Setup(object):
            def get_required_paths(self):
                return ["data"]

        def get_list(self):
            with io.open(os.path.join(self.data_dir, "data"), "r", encoding="utf-8") as f:
                return f.read().splitlines()

    class Writer(object):
        required_tasks = ["list"]

        def write_list(self, l):
            # Write out the data file
            with io.open(os.path.join(self.data_dir, "data"), "w", encoding="utf-8") as f:
                f.write(u"\n".join(l))
            self.task_complete("list")
