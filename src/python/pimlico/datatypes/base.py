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
as far as possible, these should be converted into standard datatypes like
:class:`~pimlico.datatypes.tar.TarredCorpus`, early in the pipeline.

.. note::

   The following classes were moved to :mod:`~pimlico.datatypes.core` in version 0.6rc

"""
import cPickle as pickle
import os
import re
import json
from traceback import format_exc

from pimlico.cli.shell.base import ShellCommand
from pimlico.datatypes.documents import RawDocumentType
from pimlico.utils.core import import_member
from pimlico.utils.progress import get_progress_bar

__all__ = [
    "PimlicoDatatype", "PimlicoDatatypeWriter", "IterableCorpus", "IterableCorpusWriter",
    "DynamicOutputDatatype", "DynamicInputDatatypeRequirement",
    "InvalidDocument",
    "DatatypeLoadError", "DatatypeWriteError",
    "load_datatype", "MultipleInputs",
]


_class_name_word_boundary = re.compile(r"([a-z])([A-Z])")


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

    Datatypes may supply a set of additional datatypes. These should be guaranteed to be available if the
    main datatype is available. They must require no extra processing to be made available, unless that
    is done on the fly while reading the datatype (like a filter) or while the main datatype is being
    written.

    Additional datatypes can be accessed in config files by specifying the main datatype (as a previous module,
    optionally with an output name) and the additional datatype name in the form `main_datatype->additional_name`.
    Multiple additional names may be given, causing the next name to be looked up as an additional
    datatype of the initially loaded additional datatype. E..g `main_datatype->additional0->additional1`.

    To avoid conflicts in the metadata between datatypes using the same directory, datatypes loaded as additional
    datatypes have their additional name available to them and use it as a prefix to the metadata filename.

    If `use_main_metadata=True` on an additional datatype, the same metadata will be read as for the main
    datatype to which this is an additional datatype.

    `module` is the ModuleInfo instance for the pipeline module that this datatype was produced by. It may
    be None, if the datatype wasn't instantiated by a module. It is not required to be set if you're
    instantiating a datatype in some context other than module output. It should generally be set for
    input datatypes, though, since they are treated as being created by a special input module.

    """
    datatype_name = "base_datatype"
    requires_data_preparation = False
    input_module_options = {}
    """
    Override to provide shell commands specific to this datatype. Should include the superclass' list.
    """
    shell_commands = []
    """
    List of additional datatypes provided by this one, given as (name, datatype class) pairs.
    For each of these, a call to `get_additional_datatype(name)` (once the main datatype is ready) should return a
    datatype instance that is also ready.

    """
    supplied_additional = []
    """
    Most datatype classes define their own type of corpus, which is often a subtype of some other. Some, however,
    emulate another type and it is that type that should be considered the be the type of the dataset, not the
    class itself.

    For example, TarredCorpusFilter dynamically produces something that looks like a TarredCorpus,
    and further down the pipeline, if its type is need, it should be considered to be a TarredCorpus.

    Most of the time, this can be left empty, but occasionally it needs to be set.

    """
    emulated_datatype = None

    def __init__(self, base_dir, pipeline, module=None, additional_name=None, use_main_metadata=False, **kwargs):
        self.use_main_metadata = use_main_metadata
        self.additional_name = additional_name
        self.pipeline = pipeline
        self.base_dir = base_dir
        # Search for an absolute path to the base dir that exists
        self.absolute_base_dir = pipeline.find_data_path(base_dir) if self.base_dir is not None else None
        self.data_dir = os.path.join(self.absolute_base_dir, "data") if self.absolute_base_dir is not None else None
        self.module = module
        self._metadata_filename = None

        self.options = kwargs
        # Set default options from the input module options
        # If loading as an input datatype, these will already have been set, but otherwise they might not be present
        for opt_name, opt_dict in self.input_module_options.iteritems():
            if opt_name not in self.options:
                self.options[opt_name] = opt_dict.get("default", None)

        # If the overriding class doesn't set datatype_name, we should default to something sensible
        if self.datatype_name == "base_datatype" and type(self) is not PimlicoDatatype:
            # Build a better name out of the class name
            self.datatype_name = _class_name_word_boundary.sub(r"\1_\2", type(self).__name__).lower()

    def _get_metadata(self):
        """
        Read in metadata from a file in the corpus directory.

        Note that this is no longer cached in memory. We need to be sure that the metadata values returned are
        always up to date with what is on disk, so always re-read the file when we need to get a value from
        the metadata. Since the file is typically small, this is unlikely to cause a problem. If we decide to
        return to cacheing the metadata dictionary in future, we will need to make sure that we can never run into
        problems with out-of-date metadata being returned.

        """
        if self._metadata_filename is None and self.absolute_base_dir is not None:
            # Not previously been able to access metadata, but corpus dir appears to be available now
            if self.additional_name is None or self.use_main_metadata:
                metadata_filename = "corpus_metadata"
            else:
                metadata_filename = "%s_corpus_metadata" % self.additional_name

            self._metadata_filename = os.path.join(self.absolute_base_dir, metadata_filename)

        if self._metadata_filename is not None and os.path.exists(self._metadata_filename):
            # Load dictionary of metadata
            with open(self._metadata_filename, "r") as f:
                raw_data = f.read()
                if len(raw_data) == 0:
                    # Empty metadata file: return empty metadata no matter what
                    return {}
                try:
                    # In later versions of Pimlico, we store metadata as JSON, so that it can be read in the file
                    return json.loads(raw_data)
                except ValueError:
                    # If the metadata was written by an earlier Pimlico version, we fall back to the old system:
                    # it's a pickled dictionary
                    return pickle.loads(raw_data)
        else:
            # No metadata written: data may not have been written yet
            return {}
    metadata = property(_get_metadata)

    def get_required_paths(self):
        """
        Returns a list of absolute paths to files that should be available for the data to be read.
        The base data_ready() implementation checks that these are all available and, if the datatype
        is used as an input to a pipeline and requires a data preparation routine to be run, data
        preparation will not be executed until these files are available.

        :return: list of absolute paths
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
    def create_from_options(cls, base_dir, pipeline, options={}, module=None):
        return cls(base_dir, pipeline, module=module, **options)

    def data_ready(self):
        """
        Check whether the data corresponding to this datatype instance exists and is ready to be read.

        Default implementation just checks whether the data dir exists. Subclasses might want to add their own
        checks, or even override this, if the data dir isn't needed.

        """
        # Get a list of files that the datatype depends on
        paths = self.get_required_paths()
        if paths and not all(os.path.exists(path) for path in paths):
            return False
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

    def instantiate_additional_datatype(self, name, additional_name):
        """
        Default implementation just assumes the datatype class can be instantiated using the default constructor,
        with the same base dir and pipeline as the main datatype. Options given to the main datatype are passed
        down to the additional datatype.

        """
        return dict(self.supplied_additional)[name](
            self.base_dir, self.pipeline, additional_name=additional_name, module=self.module, **self.options)

    @classmethod
    def check_type(cls, supplied_type):
        """
        Method used by datatype type-checking algorithm to determine whether a supplied datatype (given as a
        class, which is a subclass of PimlicoDatatype) is compatible with the present datatype, which is being
        treated as a type requirement.

        Typically, the present class is a type requirement on a module input and `supplied_type` is the type provided
        by a previous module's output.

        The default implementation simply checks whether `supplied_type` is a subclass of the present class. Subclasses
        may wish to impose different or additional checks.

        :param supplied_type: type provided where the present class is required, or datatype instance
        :return: True if the check is successful, False otherwise

        """
        if supplied_type.emulated_datatype is not None:
            return cls.check_type(supplied_type.emulated_datatype)
        if isinstance(supplied_type, type):
            return issubclass(supplied_type, cls)
        else:
            return isinstance(supplied_type, cls)

    @classmethod
    def type_checking_name(cls):
        """
        Supplies a name for this datatype to be used in type-checking error messages. Default implementation
        just provides the class name. Classes that override check_supplied_type() may want to override this too.

        """
        return cls.__name__

    @classmethod
    def full_datatype_name(cls):
        """
        Returns a string/unicode name for the datatype that includes relevant sub-type information. The
        default implementation just uses the attribute `datatype_name`, but subclasses may have more
        detailed information to add. For example, iterable corpus types also supply information about the
        data-point type.

        """
        return cls.datatype_name


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

    def type_checking_name(self):
        """
        Supplies a name for this datatype to be used in type-checking error messages. Default implementation
        just provides the class name. Subclasses may want to override this too.

        """
        return type(self).__name__


class MultipleInputs(object):
    """
    An input datatype that can be used as an item in a module's inputs, which lets the module accept an unbounded
    number of inputs, all satisfying the same datatype requirements. When writing the inputs in a config file,
    they can be specified as a comma-separated list of the usual type of specification (module name, with optional
    output name). Each item in the list must point to a datatype that satisfies the type-checking.

    The list may also include (or entirely consist of) a base module name from the pipeline that has been expanded
    into multiple modules according to alternative parameters (the type separated by vertical bars,
    see :ref:`parameter-alternatives`). Use the notation `*name`, where `name` is the base module name, to denote
    all of the expanded module names as inputs. These are treated as if you'd written out all of the expanded module
    names separated by commas.

    When get_input() is called on the module, instead of returning a single datatype, a list of datatypes is returned.

    """
    def __init__(self, datatype_requirements):
        self.datatype_requirements = datatype_requirements


class PimlicoDatatypeWriter(object):
    """
    Abstract base class fo data writer associated with Pimlico datatypes.

    """
    def __init__(self, base_dir, additional_name=None):
        self.additional_name = additional_name
        self.base_dir = base_dir
        self.data_dir = os.path.join(self.base_dir, "data")
        self.metadata = {}
        # Make sure the necessary directories exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        # Stores a set of output tasks that must be completed before the exit routine is called
        # Subclasses can add things to this in their init and remove them as the tasks are performed
        # The superclass exit will check that the set is empty
        self._to_output = set()

    def require_tasks(self, *tasks):
        """
        Add a name or multiple names to the list of output tasks that must be completed before writing is finished
        """
        self._to_output.update(tasks)

    def task_complete(self, task):
        if task in self._to_output:
            self._to_output.remove(task)

    def __enter__(self):
        # Store an initial version of the metadata
        self.write_metadata()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.write_metadata()
            # Check all required output tasks were completed
            if len(self._to_output):
                raise DatatypeWriteError("some outputs were not written for datatype %s: %s" %
                                         (type(self).__name__, ", ".join(self._to_output)))

    def write_metadata(self):
        if self.additional_name is None:
            metadata_filename = "corpus_metadata"
        else:
            metadata_filename = "%s_corpus_metadata" % self.additional_name

        with open(os.path.join(self.base_dir, metadata_filename), "w") as f:
            # We used to pickle the metadata dictionary, but now we store it as JSON, so it's readable
            json.dump(self.metadata, f)
            # Make sure that the file doesn't get buffered anywhere, but is fully written to disk now
            # We need to be sure that the up-to-date metadata is available immediately
            f.flush()
            os.fsync(f.fileno())

    def subordinate_additional_name(self, name):
        if self.additional_name is not None:
            return "%s->%s" % (self.additional_name, name)
        else:
            return name



class CountInvalidCmd(ShellCommand):
    """
    Data shell command to count up the number of invalid docs in a tarred corpus. Applies to any iterable corpus.

    """
    commands = ["invalid"]
    help_text = "Count the number of invalid documents in this dataset"

    def execute(self, shell, *args, **kwargs):
        corpus = shell.data
        pbar = get_progress_bar(len(corpus), title="Counting")
        invalids = sum(
            (1 if isinstance(doc, InvalidDocument) else 0) for __, doc in pbar(corpus)
        )
        print "%d / %d documents are invalid" % (invalids, len(corpus))


class IterableCorpus(PimlicoDatatype):
    """
    Superclass of all datatypes which represent a dataset that can be iterated over document by document
    (or datapoint by datapoint - what exactly we're iterating over may vary, though documents are most common).

    The actual type of the data depends on the subclass: it could be, e.g. coref output, etc. Information about
    the type of individual documents is provided by `document_type` and this is used in type checking.

    At creation time, length should be provided in the metadata, denoting how many documents are in the dataset.

    """
    datatype_name = "iterable_corpus"
    data_point_type = RawDocumentType
    shell_commands = PimlicoDatatype.shell_commands + [CountInvalidCmd()]

    def __init__(self, *args, **kwargs):
        self.raw_data = kwargs.pop("raw_data", False)
        super(IterableCorpus, self).__init__(*args, **kwargs)
        # Prepare the document datatype instance
        # Pass in all the options/kwargs we've got, which include any options that the document type specifies
        self.data_point_type_instance = self.data_point_type(self.options, self.metadata)

    def __iter__(self):
        """
        Subclasses should implement an iter method that simply iterates over all the documents in the
        corpus in a consistent order. They may also provide other methods for iterating over or otherwise
        accessing the data.

        Each yielded document should consist of a pair `(name, doc)`, where `name` is an identifier for the document
        (e.g. filename) and `doc` is the document's data, in the appropriate type.

        You may wish to call `process_document_data_with_datatype()` on the raw content to apply the data-point
        type's standard processing to it.

        """
        raise NotImplementedError

    def __len__(self):
        try:
            return self.metadata["length"]
        except KeyError:
            raise DatatypeLoadError("no length found in metadata for %s corpus. It is an iterable corpus, so if it "
                                    "is ready to use, the length should have been stored. Metadata keys found: %s" %
                                    (self.datatype_name, self.metadata.keys()))

    def get_detailed_status(self):
        return super(IterableCorpus, self).get_detailed_status() + [
            "Length: %d" % len(self)
        ]

    @classmethod
    def check_supplied_type(cls, supplied_type):
        """
        Override type checking to require that the supplied type have a document type that is compatible with
        (i.e. a subclass of) the document type of this class.
        """
        return issubclass(supplied_type, cls) and issubclass(supplied_type.document_type, cls.data_point_type)

    @classmethod
    def type_checking_name(cls):
        return "%s<%s>" % (cls.__name__, cls.data_point_type.__name__)

    @classmethod
    def full_datatype_name(cls):
        return "%s<%s>" % (cls.datatype_name, cls.data_point_type.__name__)

    def process_document_data_with_datatype(self, data):
        """
        Applies the corpus' datatype's process_document() method to the raw data
        :param data:
        :return:
        """
        # Catch invalid documents
        document = InvalidDocument.invalid_document_or_text(data)
        # Apply subclass-specific post-processing if we've not been asked to yield just the raw data
        if type(document) is not InvalidDocument and not self.raw_data:
            try:
                document = self.data_point_type_instance.process_document(document)
            except BaseException, e:
                # If there's any problem reading in the document, yield an invalid doc with the error
                document = InvalidDocument("datatype %s reader" % self.datatype_name, "%s: %s" % (e, format_exc()))
        return document


def iterable_corpus_with_data_point_type(data_point_type):
    """
    Dynamically subclass IterableCorpus to provide a version with a given data-point type.
    Most of the time, static subclasses are provided and set their data-point type appropriately, but occasionally
    for type-checking purposes it can be useful to construct a new, specialized iterable corpus on the fly.

    """
    return type(
        "%sIterableCorpus" % data_point_type.__name__,
        (IterableCorpus,),
        dict(data_point_type=data_point_type),
    )


class IterableCorpusWriter(PimlicoDatatypeWriter):
    def __exit__(self, exc_type, exc_val, exc_tb):
        super(IterableCorpusWriter, self).__exit__(exc_type, exc_val, exc_tb)
        # Check the length has been set
        if "length" not in self.metadata:
            raise DatatypeWriteError("writer for IterableDocumentCorpus must set a 'length' value in the metadata")


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
        if isinstance(text, InvalidDocument):
            return text
        elif text.startswith("***** EMPTY DOCUMENT *****"):
            return InvalidDocument.load(text)
        else:
            return text


class TypeFromInput(DynamicOutputDatatype):
    """
    Infer output type from the type of an input. Passes the type through exactly, except where the input
    datatype provides an `emulated_datatype`.

    Input name may be given. Otherwise, the default input is used.

    """
    datatype_name = "same as input corpus"

    def __init__(self, input_name=None):
        self.input_name = input_name

    def get_datatype(self, module_info):
        datatype = module_info.get_input_datatype(self.input_name)
        # If the input datatype emulates another, it is that other that we will produce as output
        if datatype.emulated_datatype is not None:
            datatype = datatype.emulated_datatype
        return datatype


class DatatypeLoadError(Exception):
    pass


class DatatypeWriteError(Exception):
    pass


def load_datatype(path):
    """
    Try loading a datatype class for a given path. Raises a DatatypeLoadError if it's not a valid
    datatype path.

    """
    try:
        cls = import_member(path)
    except ImportError, e:
        raise DatatypeLoadError("could not load datatype class %s: %s" % (path, e))

    if type(cls) is not type(object):
        raise DatatypeLoadError("tried to load datatype %s, but result was not a class, it was a %s" %
                                (path, type(cls).__name__))

    if not issubclass(cls, PimlicoDatatype):
        raise DatatypeLoadError("%s is not a Pimlico datatype" % path)
    return cls
