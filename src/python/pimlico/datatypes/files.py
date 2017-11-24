# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

import os
from glob import iglob, glob

from pimlico.core.modules.options import comma_separated_list, comma_separated_strings
from pimlico.datatypes.base import PimlicoDatatype, IterableCorpus, PimlicoDatatypeWriter, InvalidDocument
from pimlico.datatypes.documents import RawTextDocumentType


class File(PimlicoDatatype):
    """
    Simple datatype that supplies a single file, providing the path to it. Use ``FileCollection`` with a
    single file where possible.

    This is an abstract class: subclasses need to provide a way of getting to (e.g. storing) the filename in
    question.

    This overlaps somewhat with ``FileCollection``, but is mainly here for backwards compatibility. Future datatypes
    should prefer the use of ``FileCollection``.

    """
    datatype_name = "file"

    def data_ready(self):
        if not super(File, self).data_ready():
            return False
        try:
            # Check that the file that our path points to also exists
            if not os.path.exists(self.absolute_path):
                return False
        except IOError:
            # Subclasses may raise an IOError while trying to compute the path: in this case it's assumed not ready
            return False
        return True

    @property
    def absolute_path(self):
        raise NotImplementedError


class NamedFileCollection(PimlicoDatatype):
    """
    Abstract base datatype for datatypes that store a fixed collection of files, which have fixed names
    (or at least names that can be determined from the class). Very many datatypes fall into this category.
    Overriding this base class provides them with some common functionality, including the possibility of
    creating a union of multiple datatypes.

    The attribute ``filenames`` should specify a list of filenames contained by the datatype.

    All files are contained in the datatypes data directory. If files are stored in subdirectories, this may
    be specified in the list of filenames using ``/`` s. (Always use forward slashes, regardless of the operating
    system.)

    """
    datatype_name = "file_collection"
    filenames = []

    def data_ready(self):
        if not super(NamedFileCollection, self).data_ready():
            return False
        try:
            for filename in self.filenames:
                # Allow subdirectories of the data dir to be specified with /s
                # Check that the file that the path points to exists
                if not os.path.exists(os.path.join(self.data_dir, filename)):
                    return False
        except IOError:
            # Subclasses may raise an IOError while trying to compute the path: in this case it's assumed not ready
            return False
        return True


class NamedFileCollectionWriter(PimlicoDatatypeWriter):
    filenames = []

    def __init__(self, base_dir):
        super(NamedFileCollectionWriter, self).__init__(base_dir)
        # Make sure every file gets written
        for filename in self.filenames:
            self.require_tasks("write_%s" % filename)

    def write_file(self, filename, data):
        if filename not in self.filenames:
            raise ValueError("filename '%s' is not among the file collection's filenames" % filename)
        with open(os.path.join(self.data_dir, filename), "w") as f:
            f.write(data)
        self.task_complete("write_%s" % filename)


def named_file_collection_union(*file_collection_classes, **kwargs):
    """
    Takes a number of subclasses of ``FileCollection`` and produces a new datatype that shares the functionality
    of all of them and is constituted of the union of the filenames.

    The datatype name of the result will be produced automatically from the inputs, unless the kwargs ``name``
    is given to specify a new one.

    Note that the input classes' ``__init__``s will each be called once, with the standard ``PimlicoDatatype``
    args. If this behaviour does not suit the datatypes you're using, override the init or define the
    union some other way.

    """
    from collections import Counter

    if not all(issubclass(c, NamedFileCollection) for c in file_collection_classes):
        raise TypeError("cannot create file collection union type of %s, since they are not all FileCollection "
                        "subclasses" % ", ".join(c.__name__ for c in file_collection_classes))

    union_datatype_name = kwargs.get("name", "U(%s)" % ",".join(d.datatype_name for d in file_collection_classes))
    filenames_union = sum((d.filenames for d in file_collection_classes), [])
    # Check there's no overlap between the filenames from the inputs
    dup_names = [name for (name, count) in Counter(filenames_union).items() if count > 1]
    if len(dup_names):
        raise TypeError("cannot produce union file collection datatype %s, since some filenames overlap between "
                        "input types: %s" % (union_datatype_name, ", ".join(dup_names)))

    class _FileCollectionUnion(NamedFileCollection):
        datatype_name = union_datatype_name
        filenames = filenames_union

        def __init__(self, *args, **kwargs):
            super(_FileCollectionUnion, self).__init__(*args, **kwargs)
            # Instantiate each of the collection types using the same directory
            self.collection_instances = [
                d(*args, **kwargs) for d in file_collection_classes
            ]

        def __getattr__(self, item):
            # First try getting the attr from the main class
            try:
                return getattr(super(_FileCollectionUnion, self), item)
            except AttributeError:
                # No such attribute on the main class, try getting it from each of the collection classes
                for d in self.collection_instances:
                    if hasattr(d, item):
                        return getattr(d, item)
                raise AttributeError("no attr '%s' on file collection instance or any of the instances in the "
                                     "collection" % item)

    return _FileCollectionUnion


def filename_with_range(val):
    """ Option processor for file paths with an optional start and end line at the end. """
    if ":" in val:
        path, __, range = val.rpartition(":")
        if "-" not in range:
            raise ValueError("invalid line range specifier '%s' in file path" % range)
        start, __, end = range.partition("-")
        if len(start) == 0:
            start = 0
        if len(end) == 0:
            end = -1

        try:
            start = int(start)
            end = int(end)
        except ValueError:
            raise ValueError("invalid line range specifier '%s' in file path" % range)
        return path, start, end
    else:
        return val, 0, -1


comma_separated_paths = comma_separated_list(filename_with_range)


class UnnamedFileCollection(IterableCorpus):
    """
    .. note::

       Datatypes used for reading input data are being phased out and replaced by input reader modules.
       Use :mod:`pimlico.modules.input.text.raw_text_files` instead of this for reading raw text files
       at the start of your pipeline.

    A file collection that's just a bunch of files with arbitrary names. The names are not necessarily
    known until the data is ready. They may be specified as a list in the metadata, or through
    datatype options, in the case of input datatypes.

    This datatype is particularly useful for loading individual files or sets of files at the start of a
    pipeline. If you just want the raw data from each file, you can use this class as it is. It's an
    ``IterableCorpus`` with a raw data type. If you want to apply some special processing to each file,
    do so by overriding this class and specifying the ``data_point_type``, providing a ``DataPointType``
    subclass that does the necessary processing.

    When using it as an input datatype to load arbitrary files, specify a list of absolute paths to the
    files you want to use. They must be absolute paths, but remember that you can make use of various
    :doc:`special substitutions in the config file </core/config>` to give paths relative to your project
    root, or other locations.

    The file paths may use `globs <https://docs.python.org/2/library/glob.html>`_ to match multiple files.
    By default, it is assumed that every filename should exist and every glob should match at least one
    file. If this does not hold, the dataset is assumed to be not ready. You can override this by placing
    a ``?`` at the start of a filename/glob, indicating that it will be included if it exists, but is
    not depended on for considering the data ready to use.

    The same postprocessing will be applied to every file. In cases where you need to apply different
    processing to different subsets of the files, define multiple input modules, with different data
    point types, for example, and then combine them using :mod:`pimlico.modules.corpora.concat`.

    """
    datatype_name = "unnamed_file_collection"
    input_module_options = {
        "files": {
            "help": "Comma-separated list of absolute paths to files to include in the collection. Paths may include "
                    "globs. Place a '?' at the start of a filename to indicate that it's optional. You can specify "
                    "a line range for the file by adding ':X-Y' to the end of the path, where X is the first line "
                    "and Y the last to be included. Either X or Y may be left empty. (Line numbers are 1-indexed.)",
            "type": comma_separated_paths,
            "required": True,
        },
        "exclude": {
            "help": "A list of files to exclude. Specified in the same way as `files` (except without line ranges). "
                    "This allows you to specify a glob in `files` and then exclude individual files from it (you "
                    "can use globs here too)",
            "type": comma_separated_strings,
        },
    }

    def data_ready(self):
        if not super(UnnamedFileCollection, self).data_ready():
            return False
        # Get the list of paths, either from the options or the metadata
        try:
            self.get_paths(error_on_missing=True)
        except IOError:
            return False
        return True

    def get_paths(self, error_on_missing=False):
        if self.options.get("files", None) is not None:
            # Input datatype, specifying its files as a list of absolute paths
            paths = self.get_paths_from_options(error_on_missing=error_on_missing)
        else:
            # Stored datatype, specifying its files as a list in a text file
            # Read in the text file to get the list of paths
            paths = self.metadata.get("file_list", [])
            paths = [fn if os.path.abspath(fn) else os.path.join(self.data_dir, fn) for fn in paths]
            # Add dummy start and end lines
            paths = [(fn, 0, -1) for fn in paths]
            # If asked to error on missing files, check the files exist
            if error_on_missing and not all(os.path.exists(p) for (p, s, e) in paths):
                raise IOError("non-existent files in stored file_list: %s" %
                              ", ".join(p for (p, s, e) in paths if not os.path.exists(p)))
        return paths

    def get_paths_from_options(self, error_on_missing=False):
        """
        Get a list of paths to all the files specified in the ``files`` option. If ``error_on_missing=True``,
        non-optional paths or globs that do not correspond to an existing file cause an IOError to be raised.

        """
        input_fns = self.options["files"]
        paths = []
        for input_fn, s, e in input_fns:
            optional = False
            if input_fn.startswith("?"):
                # Optional path, don't error if the file doesn't exist
                optional = True
                input_fn = input_fn[1:]
            # Interpret the path as a glob
            # If it's not a glob, it will just give us one path
            matching_paths = glob(input_fn)
            # Only interested in files, not directories
            matching_paths = [p for p in matching_paths if os.path.isfile(p)]
            # Sort matching paths alphabetically, to be sure that they're always in the same order
            matching_paths.sort()
            # If no paths match, either the path was a glob that didn't match anything or a non-existent file
            if len(matching_paths) == 0 and not optional and error_on_missing:
                raise IOError("path '%s' does not exist, or is a glob that matches nothing" % input_fn)
            paths.extend([(p, s, e) for p in matching_paths])

        if self.options["exclude"] is not None:
            for excl_path in self.options["exclude"]:
                # Treat this as a glob too
                excl_matching_paths = glob(excl_path)
                paths = [(p, s, e) for (p, s, e) in paths if p not in excl_matching_paths]
        return paths

    def path_name_to_doc_name(self, path):
        return os.path.basename(path)

    def __iter__(self):
        # Use the file basenames as doc names where possible, but make sure they're unique
        used_doc_names = set()
        paths = self.get_paths()
        if len(paths):
            for path, start, end in paths:
                doc_name = self.path_name_to_doc_name(path)
                distinguish_id = 0
                # Keep increasing the distinguishing ID until we have a unique name
                while doc_name in used_doc_names:
                    base, ext = os.path.splitext(doc_name)
                    doc_name = "%s-%d%s" % (base, distinguish_id, ext)
                    distinguish_id += 1
                used_doc_names.add(doc_name)

                with open(path, "r") as f:
                    data = f.read()

                if start != 0 or end != -1:
                    # start=0 (i.e. no cutting) is the same as start=1 (start from first line)
                    if start != 0:
                        # Otherwise, shift down to account for 1-indexing
                        start -= 1
                    if end != -1:
                        end -= 1

                    lines = data.split("\n")
                    if end == -1:
                        data = "\n".join(lines[start:])
                    else:
                        data = "\n".join(lines[start:end+1])

                yield doc_name, self.process_document_data_with_datatype(data)

    def __len__(self):
        return len(self.get_paths())


class UnnamedFileCollectionWriter(PimlicoDatatypeWriter):
    """
    Use as a context manager to write a bag of files out to the output directory.

    Provide each file's raw data and a filename to use to the function `write_file()` within the `with`
    statement. The writer will keep track of what files you've output and store the list.

    """
    def __init__(self, *args, **kwargs):
        super(UnnamedFileCollectionWriter, self).__init__(*args, **kwargs)
        self.written_filenames = []

    def write_file(self, filename, data):
        with open(os.path.join(self.data_dir, filename), "w") as f:
            f.write(data)
        self.written_filenames.append(filename)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Put the list of written files in the metadata, so it gets written out
            self.metadata["file_list"] = self.written_filenames
        super(UnnamedFileCollectionWriter, self).__exit__(exc_type, exc_val, exc_tb)


def NamedFile(name):
    """
    Datatype factory that produces something like a ``File`` datatype, pointing to a single file, but doesn't store
    its path, just refers to a particular file in the data dir.

    :param name: name of the file
    :return: datatype class
    """
    class _NamedFile(NamedFileCollection):
        datatype_name = "named_file"
        filenames = [name]

        @classmethod
        def datatype_full_class_name(cls):
            return ":func:`~pimlico.datatypes.files.NamedFile`"

        @property
        def filename(self):
            return self.filenames[0]

    _NamedFile.__name__ = 'NamedFile'
    return _NamedFile


class NamedFileWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir, filename, **kwargs):
        super(NamedFileWriter, self).__init__(base_dir, **kwargs)
        self.filename = filename

    @property
    def absolute_path(self):
        return os.path.join(self.data_dir, self.filename)

    def write_data(self, data):
        """
        Write the given string data to the appropriate output file
        """
        with open(self.absolute_path, "w") as f:
            f.write(data)


class RawTextFiles(UnnamedFileCollection):
    """
    Essentially the same as RawTextDirectory, but more flexible. Should generally be used in preference to
    RawTextDirectory.

    Basic datatype for reading in all the files in a collection as raw text documents.

    Generally, this may be appropriate to use as the input datatype at the start of a pipeline. You'll then
    want to pass it through a tarred corpus filter to get it into a suitable form for input to other modules.

    """
    data_point_type = RawTextDocumentType


class RawTextDirectory(IterableCorpus):
    """
    Basic datatype for reading in all the files in a directory and its subdirectories as raw text documents.

    Generally, this may be appropriate to use as the input datatype at the start of a pipeline. You'll then
    want to pass it through a tarred corpus filter to get it into a suitable form for input to other modules.

    """
    datatype_name = "raw_text_directory"
    input_module_options = {
        "path": {
            "help": "Full path to the directory containing the files",
            "required": True,
        },
        "encoding": {
            "help": "Encoding used to store the text. Should be given as an encoding name known to Python. By "
                    "default, assumed to be 'utf8'",
            "default": "utf8",
        },
        "encoding_errors": {
            "help": "What to do in the case of invalid characters in the input while decoding (e.g. illegal utf-8 "
                    "chars). Select 'strict' (default), 'ignore', 'replace'. See Python's str.decode() for details",
            "default": "strict",
        },
    }
    data_point_type = RawTextDocumentType
    requires_data_preparation = True

    def prepare_data(self, output_dir, log):
        log.info("Counting files in input directory")
        # Walk over the entire subdirectory structure at the given path
        num_docs = sum(1 for __ in self.walk())

        with PimlicoDatatypeWriter(output_dir) as datatype:
            datatype.metadata["length"] = num_docs

    def walk(self):
        base_path = self.options["path"]
        for base_dir, subdirs, filenames in os.walk(base_path):
            for filename in filenames:
                yield os.path.join(base_dir, filename)

    def filter_document(self, doc):
        """
        Each document is passed through this filter before being yielded.
        Default implementation does nothing, but this makes it easy to implement custom postprocessing
        by overriding.
        """
        return doc

    def __iter__(self):
        base_path = self.options["path"]
        encoding = self.options["encoding"]
        errors = self.options["encoding_errors"]

        for file_path in self.walk():
            with open(file_path, "r") as f:
                # Use the file's path within the base directory as its doc name
                rel_path = os.path.relpath(file_path, base_path)
                data = f.read().decode(encoding, errors=errors)
                # Apply datatype-specific processing of the data
                document = self.process_document_data_with_datatype(data)
                # Allow subclasses to apply filters to the data
                if not isinstance(document, InvalidDocument) and not self.raw_data:
                    document = self.filter_document(document)
                yield rel_path, document

    def get_required_paths(self):
        return [self.options["path"]]
