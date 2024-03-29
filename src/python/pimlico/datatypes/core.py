# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

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
    datatype_supports_python2 = True

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
    datatype_supports_python2 = True

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


class IntValue(PimlicoDatatype):
    """
    Stores a single integer.

    """
    datatype_name = "int"
    datatype_supports_python2 = True

    class Reader(object):
        class Setup(object):
            def get_required_paths(self):
                return ["data"]

        def get_value(self):
            with io.open(os.path.join(self.data_dir, "data"), "r") as f:
                return int(f.read())

        def __int__(self):
            return self.get_value()

    class Writer(object):
        required_tasks = ["val"]

        def write_value(self, val):
            with io.open(os.path.join(self.data_dir, "data"), "w", encoding="utf-8") as f:
                f.write(str(val))
            self.task_complete("val")


class FloatValue(PimlicoDatatype):
    """
    Stores a single float.

    """
    datatype_name = "float"
    datatype_supports_python2 = True

    class Reader(object):
        class Setup(object):
            def get_required_paths(self):
                return ["data"]

        def get_value(self):
            with io.open(os.path.join(self.data_dir, "data"), "r") as f:
                return float(f.read())

        def __float__(self):
            return self.get_value()

    class Writer(object):
        required_tasks = ["val"]

        def write_value(self, val):
            with io.open(os.path.join(self.data_dir, "data"), "w", encoding="utf-8") as f:
                f.write(str(val))
            self.task_complete("val")
