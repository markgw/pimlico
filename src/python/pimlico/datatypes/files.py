# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
File collections and files.

There used to be an UnnamedFileCollection, which has been removed in the move to the
new datatype system. It used to be used mostly for input datatypes, which don't exist
any more. There may still be a use for this, though, so I may be added in future.

.. todo::

   Add a unittest for these datatypes

"""

import os
from collections import OrderedDict

from pimlico.core.modules.options import comma_separated_strings
from pimlico.datatypes import PimlicoDatatype, DynamicInputDatatypeRequirement
from pimlico.utils.core import cached_property


class NamedFileCollection(PimlicoDatatype):
    """
    Datatypes that stores a fixed collection of files, which have fixed names
    (or at least names that can be determined from the class). Very many datatypes fall into this category.
    Overriding this base class provides them with some common functionality, including the possibility of
    creating a union of multiple datatypes.

    The datatype option ``filenames`` should specify a list of filenames contained by the datatype.
    For typechecking, the provided type must have at least all the filenames of the type requirement,
    though it may include more.

    All files are contained in the datatypes data directory. If files are stored in subdirectories, this may
    be specified in the list of filenames using ``/`` s. (Always use forward slashes, regardless of the operating
    system.)

    """
    datatype_name = "named_file_collection"
    datatype_options = OrderedDict([
        ("filenames", {
            "type": comma_separated_strings,
            "help": "Filenames contained in the collection",
        })
    ])

    def __init__(self, *args, **kwargs):
        super(NamedFileCollection, self).__init__(*args, **kwargs)
        self.filenames = self.options["filenames"]

    def check_type(self, supplied_type):
        if not super(NamedFileCollection, self).check_type(supplied_type):
            return False
        # Additionally check the filenames
        # All of our filenames should be included in the supplied type
        # If there are others too, that's fine
        for reqd_fn in self.filenames:
            if reqd_fn not in supplied_type.filenames:
                return False
        return True

    class Reader:
        class Setup:
            def get_required_paths(self):
                # Split on /s, so we use the filesystem's appropriate joiner for paths
                # Just returns the paths relative to the data dir: the base setup will handle checking for them
                return super(NamedFileCollection.Reader.Setup, self).get_required_paths() + [
                    os.path.join(*filename.split("/")) for filename in self.datatype.filenames
                ]

        def process_setup(self):
            self.filenames = self.datatype.filenames

        def get_absolute_path(self, filename):
            if filename not in self.filenames:
                raise ValueError("'{}' is not a filename in the file collection".format(filename))
            return os.path.join(self.data_dir, filename)

        @cached_property
        def absolute_filenames(self):
            return [self.get_absolute_path(f) for f in self.filenames]

        def read_file(self, filename=None, mode="r"):
            # By default, read the first file in the collection
            if filename is None:
                filename = self.filenames[0]
            with open(self.get_absolute_path(filename), mode=mode) as f:
                return f.read()

        def read_files(self, mode="r"):
            return [self.read_file(f, mode=mode) for f in self.filenames]

    class Writer:
        def __init__(self, *args, **kwargs):
            super(NamedFileCollection.Writer, self).__init__(*args, **kwargs)
            self.filenames = self.datatype.filenames
            # Make sure every file gets written
            for filename in self.filenames:
                self.require_tasks("write_%s" % filename)

        def write_file(self, filename, data):
            path = self.get_absolute_path(filename)
            with open(path, "w") as f:
                f.write(data)
            self.file_written(filename)

        def file_written(self, filename):
            """ Mark the given file as having been written, if write_file() was not used to write it. """
            self.task_complete("write_%s" % filename)

        def get_absolute_path(self, filename):
            if filename not in self.filenames:
                raise ValueError("'{}' is not a filename in the file collection".format(filename))
            return os.path.join(self.data_dir, filename)


class NamedFile(NamedFileCollection):
    """
    Like NamedFileCollection, but always has exactly one file.

    The filename is given as the `filename` datatype option, which can also be given
    as the first init arg: `NamedFile("myfile.txt")`.

    """
    datatype_name = "named_file"
    datatype_options = OrderedDict([
        ("filename", {
            "help": "The file's name",
        })
    ])

    def __init__(self, *args, **kwargs):
        super(NamedFile, self).__init__(*args, **kwargs)
        self.filename = self.options["filename"]
        # Set filenames from our filename
        self.filenames = [self.filename]


class FilesInput(DynamicInputDatatypeRequirement):
    datatype_doc_info = "A file collection containing at least one file (or a given specific number). " \
                        "No constraint is put on the name of the file(s). Typically, the module will just " \
                        "use whatever the first file(s) in the collection is"

    def __init__(self, min_files=1):
        self.min_files = min_files

    def check_type(self, supplied_type):
        return isinstance(supplied_type, NamedFileCollection) and len(supplied_type.filenames) >= self.min_files


# Alias FilesInput as FileInput: the default min no. files is 1, so this makes sense, but is easier to read
# if only one file is expected
FileInput = FilesInput
