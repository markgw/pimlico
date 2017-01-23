import os

from pimlico.datatypes.base import PimlicoDatatype, IterableCorpus, PimlicoDatatypeWriter, InvalidDocument
from pimlico.datatypes.documents import RawTextDocumentType


class File(PimlicoDatatype):
    """
    Simple datatype that supplies a single file, providing the path to it.

    This is an abstract class: subclasses need to provide a way of getting to (e.g. storing) the filename in
    question.

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


def NamedFile(name):
    """
    Datatype factory that produces something like a `File` datatype, pointing to a single file, but doesn't store
    its path, just refers to a particular file in the data dir.

    :param name: name of the file
    :return: datatype class
    """
    class _NamedFile(File):
        datatype_name = "named_file"
        filename = name

        @property
        def absolute_path(self):
            return os.path.join(self.data_dir, name)

        @classmethod
        def datatype_full_class_name(cls):
            return ":func:`~pimlico.datatypes.files.NamedFile`"

    _NamedFile.__name__ = 'NamedFile'
    return _NamedFile


class NamedFileWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir, filename, *kwargs):
        super(NamedFileWriter, self).__init__(base_dir, *kwargs)
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
        }
    }
    data_point_type = RawTextDocumentType
    requires_data_preparation = True

    def data_ready(self):
        return super(RawTextDirectory, self).data_ready() and os.path.exists(self.options["path"])

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

        for file_path in self.walk():
            with open(file_path, "r") as f:
                # Use the file's path within the base directory as its doc name
                rel_path = os.path.relpath(file_path, base_path)
                data = f.read().decode(encoding)
                # Apply datatype-specific processing of the data
                document = self.process_document_data_with_datatype(data)
                # Allow subclasses to apply filters to the data
                if not isinstance(document, InvalidDocument) and not self.raw_data:
                    document = self.filter_document(document)
                yield rel_path, document

    def get_required_paths(self):
        return [self.options["path"]]
