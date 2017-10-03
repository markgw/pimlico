import os

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


class FileCollection(PimlicoDatatype):
    """
    Abstract base datatype for datatypes that store a fixed collection of files, which have fixed names
    (or at least names that can be determined from the class). Very many datatypes fall into this category.
    Overriding this base class provides them with some common functionality, including the possibility of
    creating a union of multiple datatypes.

    The attribute ``filenames`` should specify a list of filenames contained by the datatype.

    All files are contained in the datatypes data directory. If files are stored in subdirectories, this may
    be specified in the list of filenames using ``/``s. (Always use forward slashes, regardless of the operating
    system.)

    """
    datatype_name = "file_collection"
    filenames = []

    def data_ready(self):
        if not super(FileCollection, self).data_ready():
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


class FileCollectionWriter(PimlicoDatatypeWriter):
    filenames = []

    def __init__(self, base_dir):
        super(FileCollectionWriter, self).__init__(base_dir)
        # Make sure every file gets written
        for filename in self.filenames:
            self.require_tasks("write_%s" % filename)

    def write_file(self, filename, data):
        if filename not in self.filenames:
            raise ValueError("filename '%s' is not among the file collection's filenames" % filename)
        with open(os.path.join(self.data_dir, filename), "w") as f:
            f.write(data)
        self.task_complete("write_%s" % filename)


def file_collection_union(*file_collection_classes, **kwargs):
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

    if not all(issubclass(c, FileCollection) for c in file_collection_classes):
        raise TypeError("cannot create file collection union type of %s, since they are not all FileCollection "
                        "subclasses" % ", ".join(c.__name__ for c in file_collection_classes))

    union_datatype_name = kwargs.get("name", "U(%s)" % ",".join(d.datatype_name for d in file_collection_classes))
    filenames_union = sum((d.filenames for d in file_collection_classes), [])
    # Check there's no overlap between the filenames from the inputs
    dup_names = [name for (name, count) in Counter(filenames_union).items() if count > 1]
    if len(dup_names):
        raise TypeError("cannot produce union file collection datatype %s, since some filenames overlap between "
                        "input types: %s" % (union_datatype_name, ", ".join(dup_names)))

    def __init__(self, *args, **kwargs):
        super(_FileCollectionUnion, self).__init__(*args, **kwargs)
        for d in file_collection_classes:
            d.__init__(self, *args, **kwargs)

    def __getattr__(self, item):
        # Try getting this attr from each of the classes in the union
        for d in file_collection_classes:
            if hasattr(d, item):
                return getattr(d, item)
        # None of the classes has such an attribute
        # Pass up to the super to process this: either it will find the attr on this class or raise
        return getattr(super(_FileCollectionUnion, self), item)

    _FileCollectionUnion = type("_FileCollectionUnion", file_collection_classes, {
        "datatype_name": union_datatype_name,
        "filenames": filenames_union,
        "__init__": __init__,
        "__getattr__": __getattr__,
    })

    return _FileCollectionUnion


def NamedFile(name):
    """
    Datatype factory that produces something like a ``File`` datatype, pointing to a single file, but doesn't store
    its path, just refers to a particular file in the data dir.

    :param name: name of the file
    :return: datatype class
    """
    class _NamedFile(FileCollection):
        datatype_name = "named_file"
        filenames = [name]

        @classmethod
        def datatype_full_class_name(cls):
            return ":func:`~pimlico.datatypes.files.NamedFile`"

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
