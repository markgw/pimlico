# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
File collections and files.

There used to be an UnnamedFileCollection, which has been removed in the move to the
new datatype system. It used to be used mostly for input datatypes, which don't exist
any more. There may still be a use for this, though, so I may be added in future.

"""

import io
import os
from collections import OrderedDict

from builtins import object

from pimlico.core.modules.options import comma_separated_strings
from pimlico.datatypes import PimlicoDatatype, DynamicInputDatatypeRequirement
from pimlico.utils.core import cached_property

__all__ = ["NamedFileCollection", "NamedFile", "FilesInput", "FileInput", "TextFile"]


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
            "default": [],
        })
    ])
    datatype_supports_python2 = True

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

    def browse_file(self, reader, filename):
        """
        Return text for a particular file in the collection to show in the
        browser. By default, just reads in the file's data and returns
        it, but subclasses might want to override this (perhaps conditioned
        on the filename) to format the data readably.

        :param reader:
        :param filename:
        :return: file data to show
        """
        return reader.read_file(filename)

    def run_browser(self, reader, opts):
        """
        All NamedFileCollections provide a browser that just lets you see a
        list of the files and view them, in the case of text files.

        Subclasses may override the way individual files are shown by
        overriding `browse_file()`.

        """
        from pimlico.cli.browser.tools.files import browse_files
        browse_files(reader)

    class Reader(object):
        class Setup(object):
            def get_required_paths(self):
                # Split on /s, so we use the filesystem's appropriate joiner for paths
                # Just returns the paths relative to the data dir: the base setup will handle checking for them
                return super(NamedFileCollection.Reader.Setup, self).get_required_paths() + [
                    os.path.join(*filename.split("/")) for filename in self.datatype.filenames
                ]

        def process_setup(self):
            super(NamedFileCollection.Reader, self).process_setup()
            self.filenames = self.datatype.filenames

        def get_absolute_path(self, filename):
            if filename not in self.filenames:
                raise ValueError("'{}' is not a filename in the file collection".format(filename))
            return os.path.join(self.data_dir, filename)

        @cached_property
        def absolute_paths(self):
            return [self.get_absolute_path(f) for f in self.filenames]

        @property
        def absolute_filenames(self):
            """ For backwards compatibility: use absolute_paths by preference """
            return self.absolute_paths

        def read_file(self, filename=None, mode="r", text=False):
            """
            Read a file from the collection.

            :param filename: string filename, which should be one of the filenames specified for this
                collection; or an integer, in which case the ith file in the collection is read. If
                not given, the first file is read
            :param mode:
            :param text: if True, the file is treated as utf-8-encoded text and a unicode object is
                returned. Otherwise, a bytes object is returned.
            :return:
            """
            with self.open_file(filename, mode=mode) as f:
                data = f.read()
            if text:
                return data.decode("utf-8")
            else:
                return data

        def read_files(self, mode="r", text=False):
            return [self.read_file(f, mode=mode, text=text) for f in self.filenames]

        def open_file(self, filename=None, mode="r"):
            # By default, read the first file in the collection
            if filename is None:
                filename = self.filenames[0]
            elif type(filename) is int:
                # Allow an int to specify the ith filename
                filename = self.filenames[filename]
            return OpenFileReader(self, filename, mode=mode)

    class Writer(object):
        def __init__(self, *args, **kwargs):
            super(NamedFileCollection.Writer, self).__init__(*args, **kwargs)
            self.filenames = self.datatype.filenames
            # Make sure every file gets written
            for filename in self.filenames:
                self.require_tasks("write_%s" % filename)

        def write_file(self, filename, data, text=False):
            """
            If text=True, the data is expected to be unicode and is encoded as utf-8.
            Otherwise, data should be a bytes object.

            """
            # The filename could contain a subdirectory, so check the dir exists
            file_dir = os.path.dirname(self.get_absolute_path(filename))
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            if text:
                data = data.encode("utf-8")
            # Write the file
            with self.open_file(filename) as f:
                f.write(data)

        def file_written(self, filename):
            """ Mark the given file as having been written, if write_file() was not used to write it. """
            self.task_complete("write_%s" % filename)

        def open_file(self, filename=None):
            if filename is None:
                filename = self.filenames[0]
            return OpenFileWriter(self, filename)

        def get_absolute_path(self, filename=None):
            if filename is None:
                filename = self.filenames[0]
            elif filename not in self.filenames:
                raise ValueError("'{}' is not a filename in the file collection".format(filename))
            return os.path.join(self.data_dir, filename)

        @cached_property
        def absolute_paths(self):
            return [self.get_absolute_path(f) for f in self.filenames]


class OpenFileWriter(io.FileIO):
    def __init__(self, writer, filename):
        self.writer = writer
        self.filename = filename
        super(OpenFileWriter, self).__init__(self.writer.get_absolute_path(self.filename), "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(OpenFileWriter, self).__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            self.writer.file_written(self.filename)


class OpenFileReader(io.FileIO):
    def __init__(self, reader, filename, mode="r"):
        self.reader = reader
        self.filename = filename
        super(OpenFileReader, self).__init__(self.reader.get_absolute_path(self.filename), mode=mode)


class NamedFile(NamedFileCollection):
    """
    Like NamedFileCollection, but always has exactly one file.

    The filename is given as the `filename` datatype option, which can also be given
    as the first init arg: `NamedFile("myfile.txt")`.

    Since NamedFile is a subtype of NamedFileCollection, it also has a "filenames" option.
    It is ignored if the `filename` option is given, and otherwise must have exactly one
    item.

    """
    datatype_name = "named_file"
    datatype_options = OrderedDict([
        ("filename", {
            "help": "The file's name",
        })
    ] + list(NamedFileCollection.datatype_options.items()))
    datatype_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(NamedFile, self).__init__(*args, filenames=[], **kwargs)
        self.filename = self.options["filename"]
        if self.filename is None:
            # Allow the "filenames" option to be used as well
            if len(self.filenames) > 1:
                raise ValueError("tried to instantiate NamedFile with multiple filenames in the 'filename' option")
            elif len(self.filenames) == 1:
                self.filename = self.filenames[0]
            else:
                # Use a default filename if none is given
                self.filename = "data"

        # Set filenames from our filename
        self.filenames = [self.filename]

    class Reader(object):
        def process_setup(self):
            super(NamedFile.Reader, self).process_setup()
            self.filename = self.datatype.filename

        @property
        def absolute_path(self):
            return self.get_absolute_path(self.filename)

    class Writer(object):
        def __init__(self, *args, **kwargs):
            super(NamedFile.Writer, self).__init__(*args, **kwargs)
            self.filename = self.datatype.filename

        def write_file(self, data, text=False):
            super(NamedFile.Writer, self).write_file(self.filename, data, text=text)

        @property
        def absolute_path(self):
            return self.get_absolute_path(self.filename)


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


class TextFile(NamedFile):
    """
    Simple dataset containing just a single utf-8 encoded text file.

    """
    datatype_name = "text_document"
    datatype_options = OrderedDict([
        ("filename", {
            "help": "The file's name. Typically left as the default. Default: data.txt",
            "default": "data.txt",
        })
    ] + list(NamedFileCollection.datatype_options.items()))
    datatype_supports_python2 = True

    class Reader(object):
        def read_file(self, filename=None, mode="r", text=False):
            # Ignore filename, since there's only one
            return super(TextFile.Reader, self).read_file(text=text)

    class Writer(object):
        def write_file(self, data, text=False):
            super(TextFile.Writer, self).write_file(data, text=text)
