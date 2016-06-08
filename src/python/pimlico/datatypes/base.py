# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Datatypes provide interfaces for reading (and in some cases writing) datasets. At their most basic,
they define a way to iterate over a dataset linearly. Some datatypes may also provide other functionality,
such as random access or compression.

As much as possible, Pimlico pipelines should use standard datatypes to connect up the output of modules
with the input of others. Most datatypes have a lot in common, which should be reflected in their sharing
common base classes. Custom datatypes will be needed for most datasets when they're used as inputs, but
as far as possible, these should be converted into standard datatypes, or at least a form where they can
use standard idioms for iterating, etc, early in the pipeline.

"""
import os
from importlib import import_module

import cPickle as pickle


__all__ = [
    "PimlicoDatatype", "PimlicoDatatypeWriter", "IterableCorpus", "IterableCorpusWriter",
    "DynamicOutputDatatype", "DynamicInputDatatypeRequirement",
    "InvalidDocument",
    "DatatypeLoadError", "DatatypeWriteError",
    "load_datatype"
]


class PimlicoDatatype(object):
    """
    The abstract superclass of all datatypes. Provides basic functionality for identifying where
    data should be stored and such.

    Datatypes are used to specify the routines for reading the output from modules. They're also
    used to specify how to read pipeline inputs. Most datatypes that have data simply read it in
    when required. Some (in particular those used as inputs) need a preparation phase to be run,
    where the raw data itself isn't sufficient to implement the reading interfaces required. In this
    case, they should override prepare_data().

    Datatypes may require/allow options to be set when they're used to read pipeline inputs. These
    are specified, in the same way as module options, by input_module_options on the datatype class.

    """
    datatype_name = "base_datatype"
    requires_data_preparation = False
    input_module_options = {}
    """
    Override to provide shell commands specific to this datatype. Should include the superclass' list.
    """
    shell_commands = []

    def __init__(self, base_dir, pipeline, **kwargs):
        self.pipeline = pipeline
        self.base_dir = base_dir
        # Search for an absolute path to the base dir that exists
        self.absolute_base_dir = pipeline.find_data_path(base_dir) if self.base_dir is not None else None
        self.data_dir = os.path.join(self.absolute_base_dir, "data") if self.absolute_base_dir is not None else None
        self._metadata = None

        # This attribute setting business is left here for backwards compatibility, but you should use the options
        # dict by preference
        for attr, val in kwargs.items():
            setattr(self, attr, val)
        self.options = kwargs

    @property
    def metadata(self):
        if self._metadata is None:
            if self.absolute_base_dir is not None and \
                    os.path.exists(os.path.join(self.absolute_base_dir, "corpus_metadata")):
                # Load dictionary of metadata
                with open(os.path.join(self.absolute_base_dir, "corpus_metadata"), "r") as f:
                    self._metadata = pickle.load(f)
            else:
                # No metadata written: data may not have been written yet
                self._metadata = {}
        return self._metadata

    def check_runtime_dependencies(self):
        """
        Like the similarly named method on executors, this check dependencies for using the datatype.
        It's not called when checking basic config, but only when the datatype is needed.

        Returns a list of pairs: (dependency short name, description/error message)

        .. deprecated:: 0.2
           You should provide dependency information via :meth:`get_software_dependencies` instead. This method
           will be called as well for backward compatibility until v1.

        """
        return []

    def get_software_dependencies(self):
        """
        Check that all software required to read this datatype is installed and locatable. This is
        separate to metadata config checks, so that you don't need to satisfy the dependencies for
        all modules in order to be able to run one of them. You might, for example, want to run different
        modules on different machines. This is called when a module is about to be executed and each of the
        dependencies is checked.

        Returns a list of instances of subclasses of :class:~pimlico.core.dependencies.base.SoftwareDependency,
        representing the libraries that this module depends on.

        Take care when providing dependency classes that you don't put any import statements at the top of the Python
        module that will make loading the dependency type itself dependent on runtime dependencies.
        You'll want to run import checks by putting import statements within this method.

        You should call the super method for checking superclass dependencies.

        """
        return []

    def prepare_data(self, output_dir, log):
        return

    @classmethod
    def create_from_options(cls, base_dir, pipeline, options={}):
        return cls(base_dir, pipeline, **options)

    def data_ready(self):
        """
        Check whether the data corresponding to this datatype instance exists and is ready to be read.

        Default implementation just checks whether the data dir exists. Subclasses might want to add their own
        checks, or even override this, if the data dir isn't needed.

        """
        # If data_dir is None, the datatype doesn't need it
        # data_dir is None unless the data dir has been located
        return self.base_dir is None or self.data_dir is not None

    def get_detailed_status(self):
        """
        Returns a list of strings, containing detailed information about the data.
        Only called if data_ready() == True.

        Subclasses may override this to supply useful (human-readable) information specific to the datatype.
        They should called the super method.
        """
        return []

    @classmethod
    def datatype_full_class_name(cls):
        """
        The fully qualified name of the class for this datatype, by which it is reference in config files.
        Generally, datatypes don't need to override this, but type requirements that take the place of datatypes
        for type checking need to provide it.

        """
        return "%s.%s" % (cls.__module__, cls.__name__)


class DynamicOutputDatatype(object):
    """
    Types of module outputs may be specified as a subclass of :class:`.PimlicoDatatype`, or alternatively
    as an *instance* of DynamicOutputType. In this case, get_datatype() is called when the output datatype is
    needed, passing in the module info instance for the module, so that a specialized datatype can be
    produced on the basis of options, input types, etc.

    The dynamic type must provide certain pieces of information needed for typechecking.

    """
    """
    Must be provided by subclasses: can be a noncommittal string giving some idea of what types may be provided.
    Used for documentation.
    """
    datatype_name = None

    def get_datatype(self, module_info):
        raise NotImplementedError

    def get_base_datatype_class(self):
        """
        If it's possible to say before the instance of a ModuleInfo is available what base datatype will be
        produced, implement this to return the class. By default, it returns None.

        If this information is available, it will be used in documentation.

        """
        return None


class DynamicInputDatatypeRequirement(object):
    """
    Types of module inputs may be given as a subclass of :class:`.PimlicoDatatype`, a tuple of datatypes, or
    an instance a DynamicInputDatatypeRequirement subclass. In this case, check_type(supplied_type) is called
    during typechecking to check whether the type that we've got conforms to the input type requirements.

    Additionally, if datatype_doc_info is provided, it is used to represent the input type constraints in
    documentation.

    """
    """
    To provide a helpful message for the documentation, either override this, or set it in the constructor.
    """
    datatype_doc_info = None

    def check_type(self, supplied_type):
        raise NotImplementedError


class MultipleInputs(object):
    """
    An input datatype that can be used as an item in a module's inputs, which lets the module accept an unbounded
    number of inputs, all satisfying the same datatype requirements. When writing the inputs in a config file,
    they can be specified as a comma-separated list of the usual type of specification (module name, with optional
    output name). Each item in the list must point to a datatype that satisfies the type-checking.

    When get_input() is called on the module, instead of returning a single datatype, a list of datatypes is returned.

    """
    def __init__(self, datatype_requirements):
        self.datatype_requirements = datatype_requirements


class PimlicoDatatypeWriter(object):
    """
    Abstract base class fo data writer associated with Pimlico datatypes.

    """
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.data_dir = os.path.join(self.base_dir, "data")
        self.metadata = {}
        # Make sure the necessary directories exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write_metadata()

    def write_metadata(self):
        with open(os.path.join(self.base_dir, "corpus_metadata"), "w") as f:
            pickle.dump(self.metadata, f, -1)


class IterableCorpus(PimlicoDatatype):
    """
    Superclass of all datatypes which represent a dataset that can be iterated over document by document
    (or datapoint by datapoint - what exactly we're iterating over may vary, though documents are most common).
    The actual type of the data depends on the subclass: it could be, e.g. coref output, etc.

    At creation time, length should be provided in the metadata, denoting how many documents are in the dataset.

    """
    datatype_name = "iterable_corpus"

    def __init__(self, *args, **kwargs):
        super(IterableCorpus, self).__init__(*args, **kwargs)

    def __iter__(self):
        """
        Subclasses should implement an iter method that simply iterates over all the documents in the
        corpus in a consistent order. They may also provide other methods for iterating over or otherwise
        accessing the data.

        """
        raise NotImplementedError

    def __len__(self):
        return self.metadata["length"]

    def get_detailed_status(self):
        return super(IterableCorpus, self).get_detailed_status() + [
            "Length: %d" % len(self)
        ]


class IterableCorpusWriter(PimlicoDatatypeWriter):
    def __exit__(self, exc_type, exc_val, exc_tb):
        super(IterableCorpusWriter, self).__exit__(exc_type, exc_val, exc_tb)
        # Check the length has been set
        if "length" not in self.metadata:
            raise DatatypeWriteError("writer for IterableDocumentCorpus must set a 'length' value in the metadata")


class SingleTextDocument(PimlicoDatatype):
    datatype_name = "single_doc"

    def data_ready(self):
        return super(SingleTextDocument, self).data_ready() and os.path.exists(os.path.join(self.data_dir, "data.txt"))

    def read_data(self):
        with open(os.path.join(self.data_dir, "data.txt"), "r") as f:
            return f.read().decode("utf-8")


class SingleTextDocumentWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir):
        super(SingleTextDocumentWriter, self).__init__(base_dir)
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


class Dict(PimlicoDatatype):
    """
    Simply stores a Python dict, pickled to disk.

    """
    datatype_name = "dict"

    def data_ready(self):
        return super(Dict, self).data_ready() and os.path.exists(os.path.join(self.data_dir, "data"))

    @property
    def data(self):
        import cPickle as pickle
        with open(os.path.join(self.data_dir, "data"), "r") as f:
            return pickle.load(f)


class DictWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir):
        super(DictWriter, self).__init__(base_dir)
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
        return super(StringList, self).data_ready() and os.path.exists(os.path.join(self.data_dir, "data"))

    @property
    def data(self):
        with open(os.path.join(self.data_dir, "data"), "r") as f:
            return f.read().decode("utf-8").splitlines()


class StringListWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir):
        super(StringListWriter, self).__init__(base_dir)
        self.data = []
        self.output_path = os.path.join(self.data_dir, "data")

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(StringListWriter, self).__exit__(exc_type, exc_val, exc_tb)
        if exc_type is None:
            # Write out the data file
            with open(self.output_path, "w") as f:
                f.write((u"\n".join(self.data)).encode("utf-8"))


class InvalidDocument(object):
    """
    Widely used in Pimlico to represent an empty document that is empty not because the original input document
    was empty, but because a module along the way had an error processing it. Document readers/writers should
    generally be robust to this and simply pass through the whole thing where possible, so that it's always
    possible to work out, where one of these pops up, where the error occurred.

    """
    def __init__(self, module_name, error_info=None):
        self.error_info = error_info
        self.module_name = module_name

    def __unicode__(self):
        return u"***** EMPTY DOCUMENT *****\nEmpty due to processing error in module: %s\n\nFull error details:\n%s" % \
               (self.module_name, self.error_info or "")

    def __str__(self):
        return unicode(self).encode("ascii", "ignore")

    @staticmethod
    def load(text):
        if not text.startswith("***** EMPTY DOCUMENT *****"):
            raise ValueError("tried to read empty document text from invalid text: %s" % text)
        text = text.partition("\n")[2]
        module_line, __, text = text.partition("\n\n")
        module_name = module_line.partition(": ")[2]
        error_info = text.partition("\n")[2]
        return InvalidDocument(module_name, error_info)

    @staticmethod
    def invalid_document_or_text(text):
        """
        If the text represents an invalid document, parse it and return an InvalidDocument object.
        Otherwise, return the text as is.
        """
        if text.startswith("***** EMPTY DOCUMENT *****"):
            return InvalidDocument.load(text)
        else:
            return text


class DatatypeLoadError(Exception):
    pass


class DatatypeWriteError(Exception):
    pass


def load_datatype(path):
    """
    Try loading a datatype class for a given path. Raises a DatatypeLoadError if it's not a valid
    datatype path.

    """
    mod_path, __, cls_name = path.rpartition(".")
    try:
        mod = import_module(mod_path)
    except ImportError:
        raise DatatypeLoadError("could not load module %s" % mod_path)

    if not hasattr(mod, cls_name):
        raise DatatypeLoadError("could not load datatype class %s in module %s" % (cls_name, mod_path))
    cls = getattr(mod, cls_name)

    if type(cls) is not type(object):
        raise DatatypeLoadError("tried to load datatype %s.%s, but result was not a class, it was a %s" %
                                (mod, cls_name, type(cls).__name__))

    if not issubclass(cls, PimlicoDatatype):
        raise DatatypeLoadError("%s is not a Pimlico datatype" % path)
    return cls
