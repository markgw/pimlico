# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Datatypes provide interfaces for reading (and in some cases writing) datasets. At their most basic,
they define a way to iterate over a dataset linearly. Some datatypes may also provide other functionality,
such as random access or compression.

As much as possible, Pimlico pipelines should use standard datatypes to connect up the output of modules
with the input of others. Most datatypes have a lot in common, which should be reflected in their sharing
common base classes. Custom input modules will be needed for most datasets when they're used as inputs, but
as far as possible, these should produce standard datatypes like
:class:`~pimlico.datatypes.tar.TarredCorpus` as output.

Instances of subclasses of PimlicoDatatype represent the type of datasets and are used for typechecking
in a pipeline. Subclasses of PimlicoDatatypeReader are created automatically to correspond to each
datatype and can be instantiated via the datatype (by calling it). These perform the actual reading of
(e.g. iteration over) datasets.

A similar reflection of the datatype hierarchy is used for dataset writers, except that not all datatypes
provide a writer.

"""
import json
import os
import pickle
import re
from collections import OrderedDict

from pimlico.utils.core import import_member

__all__ = [
    "PimlicoDatatype",
    "DynamicOutputDatatype", "DynamicInputDatatypeRequirement",
    "DatatypeLoadError", "DatatypeWriteError",
    "load_datatype", "MultipleInputs",
]


_class_name_word_boundary = re.compile(r"([a-z])([A-Z])")


class PimlicoDatatype(object):
    """
    The abstract superclass of all datatypes. Provides basic functionality for identifying where
    data should be stored and such.

    Datatypes are used to specify the routines for reading the output from modules, via their reader
    class.

    `module` is the ModuleInfo instance for the pipeline module that this datatype was produced by. It may
    be None, if the datatype wasn't instantiated by a module. It is not required to be set if you're
    instantiating a datatype in some context other than module output. It should generally be set for
    input datatypes, though, since they are treated as being created by a special input module.

    """
    datatype_name = "base_datatype"
    """
    Options specified in the same way as module options that control the nature of the 
    datatype. These are not things to do with reading of specific datasets, for which 
    the dataset's metadata should be used. These are things that have an impact on 
    typechecking, such that options on the two checked datatypes are required to match 
    for the datatypes to be considered compatible.
    
    They should always be an ordered dict, so that they can be specified using 
    positional arguments as well as kwargs and config parameters.
    
    """
    datatype_options = OrderedDict()
    """
    Override to provide shell commands specific to this datatype. Should include the superclass' list.
    """
    shell_commands = []
    """
    Most datatype classes define their own type of corpus, which is often a subtype of some other. Some, however,
    emulate another type and it is that type that should be considered the be the type of the dataset, not the
    class itself.

    For example, TarredCorpusFilter dynamically produces something that looks like a TarredCorpus,
    and further down the pipeline, if its type is need, it should be considered to be a TarredCorpus.

    Most of the time, this can be left empty, but occasionally it needs to be set.

    """
    emulated_datatype = None

    def __init__(self, *args, **kwargs):
        # Kwargs specify (processed) values for named datatype options
        # Check they're all valid options
        for key in kwargs:
            if key not in self.datatype_options:
                raise DatatypeLoadError("unknown datatype option '{}' for {}".format(key, self.datatype_name))
        self.options = dict(kwargs)
        # Positional args can also be used to specify options, using the order in which the options are defined
        for key, arg in zip(self.datatype_options.iterkeys(), args):
            if key in kwargs:
                raise DatatypeLoadError("datatype option '{}' given by positional arg was also specified "
                                        "by a kwarg".format(key))
            self.options[key] = arg

        # Check any required options have been given
        for opt_name, opt_dict in self.datatype_options.iteritems():
            if opt_dict.get("required", False) and opt_name not in self.options:
                raise DatatypeLoadError("{} datatype requires option '{}' to be specified".format(
                    self.datatype_name, opt_name))
        # Finally, set default options from the datatype options
        for opt_name, opt_dict in self.datatype_options.iteritems():
            if opt_name not in self.options:
                self.options[opt_name] = opt_dict.get("default", None)

        # If the overriding class doesn't set datatype_name, we should default to something sensible
        if self.datatype_name == "base_datatype" and type(self) is not PimlicoDatatype:
            # Build a better name out of the class name
            self.datatype_name = _class_name_word_boundary.sub(r"\1_\2", type(self).__name__).lower()

    def __call__(self, base_dir, pipeline, module=None):
        """
        Instantiate a reader to read data from the given base dir (or None, if the reader doesn't
        need a base dir). Calls data_ready() first and raises a DataNotReadyError if it fails.

        """
        if not self.data_ready(base_dir):
            raise DataNotReadyError("data not ready at {}".format(base_dir))
        reader_cls = self._get_reader_cls()
        # Data is ready, so we should be able to instantiate the reader
        return reader_cls(self, base_dir, pipeline, module=module)

    def get_writer(self, base_dir, pipeline, module=None):
        """
        Instantiate a writer to write data to the given base dir.

        :param base_dir: output dir to write dataset to
        :param pipeline: current pipeline
        :param module: module name (optional, for debugging only)
        :return: instance of the writer subclass corresponding to this datatype
        """
        # TODO

    @classmethod
    def instantiate_from_options(cls, options={}):
        """Given string options e.g. from a config file, perform option processing and instantiate datatype"""
        # TODO Do preprocesing of datatype options here
        return cls(**options)

    @classmethod
    def datatype_full_class_name(cls):
        """
        The fully qualified name of the class for this datatype, by which it is reference in config files.
        Generally, datatypes don't need to override this, but type requirements that take the place of datatypes
        for type checking need to provide it.

        """
        return "%s.%s" % (cls.__module__, cls.__name__)

    def check_type(self, supplied_type):
        """
        Method used by datatype type-checking algorithm to determine whether a supplied datatype (given as an
        instance of a subclass of PimlicoDatatype) is compatible with the present datatype, which is being
        treated as a type requirement.

        Typically, the present class is a type requirement on a module input and `supplied_type` is the type provided
        by a previous module's output.

        The default implementation simply checks whether `supplied_type` is a subclass of the present class. Subclasses
        may wish to impose different or additional checks.

        :param supplied_type: type provided where the present class is required, or datatype instance
        :return: True if the check is successful, False otherwise

        """
        if supplied_type.emulated_datatype is not None:
            return self.check_type(supplied_type.emulated_datatype)
        if isinstance(supplied_type, type):
            # This is how datatypes used to be specified, but now they should be instances
            raise TypeError("type checking was given a class as a supplied type. It should be an instance "
                            "of a datatype. Probably old code from before datatypes redesign")
        else:
            return isinstance(supplied_type, type(self))

    def type_checking_name(self):
        """
        Supplies a name for this datatype to be used in type-checking error messages. Default implementation
        just provides the class name. Classes that override check_supplied_type() may want to override this too.

        """
        return type(self).__name__

    def full_datatype_name(self):
        """
        Returns a string/unicode name for the datatype that includes relevant sub-type information. The
        default implementation just uses the attribute `datatype_name`, but subclasses may have more
        detailed information to add. For example, iterable corpus types also supply information about the
        data-point type.

        """
        return self.datatype_name

    def __repr__(self):
        return self.datatype_name

    def get_required_paths(self):
        """
        Returns a list of paths to files that should be available for the data to be read.
        The base data_ready() implementation checks that these are all available.

        Paths may be absolute or relative. If relative, they refer to files within the data directory
        and data_ready() will fail if the data dir doesn't exist.

        :return: list of absolute or relative paths
        """
        return []

    def get_software_dependencies(self):
        """
        Get a list of all software required to **read** this datatype. This is
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

        Note that there may be different software dependencies for **writing** a datatype using its `Writer`.
        These should be specified using `get_writer_software_dependencies()`.

        """
        return []

    def get_writer_software_dependencies(self):
        """
        Get a list of all software required to **write** this datatype using its `Writer`. This
        works in a similar way to `get_software_dependencies()` (for the `Reader`) and the
        dependencies will be check before the writer is instantiated.

        It is assumed that all the reader's dependencies also apply to the writer, so this method
        only needs to specify any additional dependencies the writer has.

        You should call the super method for checking superclass dependencies.

        .. todo::

           Call get_writer_software_dependencies before instantiating writer

        """
        return []

    def data_ready(self, base_dir):
        """
        Check whether the data corresponding to this dataset exists and is ready to be read at
        the given base dir.

        Called before the reader is instantiated and has access to any information in the datatype
        instance. It may be called several times with different possible base dirs to check whether
        data is available at any of them.

        Default implementation just checks whether the data dir exists. Subclasses might want to add their own
        checks, or even override this, if the data dir isn't needed.

        """
        # Get a list of files that the datatype depends on
        data_dir = self._get_data_dir(base_dir)

        if base_dir is not None and not os.path.exists(data_dir):
            # base_dir may be None, meaning that it's not required
            # Otherwise, it must exist, and the data dir within it
            return False

        paths = self.get_required_paths()
        if paths:
            for path in paths:
                if os.path.abspath(path):
                    # Simply check whether the file exists
                    if not os.path.exists(path):
                        return False
                else:
                    # Relative path: requires that data_dir exists
                    if data_dir is None:
                        return False
                    elif not os.path.exists(os.path.join(data_dir, path)):
                        # Data dir is ready, but the file within it doesn't exist
                        return False
        return True

    @staticmethod
    def _get_data_dir(base_dir):
        return None if base_dir is None else os.path.join(base_dir, "data")

    class Reader:
        """
        The abstract superclass of all dataset readers.

        You do not need to subclass or instantiate these yourself: subclasses are created automatically
        to correspond to each datatype. You can add functionality to a datatype's reader by creating a
        nested `Reader` class. This will inherit from the parent datatype's reader. This happens
        automatically - you don't need to do it yourself and shouldn't inherit from anything:

        .. code-block:: py
           class MyDatatype(PimlicoDatatype):
               class Reader:
                   # Overide reader things here

        """
        def __init__(self, datatype, base_dir, pipeline, module=None):
            self.datatype = datatype
            self.pipeline = pipeline
            # Base dir should already be an absolute path to an existing directory
            # If it's None, the reader is one that doesn't need a directory (e.g. generates data)
            self.base_dir = base_dir
            self.data_dir = self.datatype._get_data_dir(base_dir)
            self.module = module
            self._metadata_filename = None

        def get_detailed_status(self):
            """
            Returns a list of strings, containing detailed information about the data.

            Subclasses may override this to supply useful (human-readable) information specific to the datatype.
            They should called the super method.

            """
            return []

        def _get_metadata(self):
            """
            Read in metadata from a file in the corpus directory.

            Note that this is no longer cached in memory. We need to be sure that the metadata values returned are
            always up to date with what is on disk, so always re-read the file when we need to get a value from
            the metadata. Since the file is typically small, this is unlikely to cause a problem. If we decide to
            return to cacheing the metadata dictionary in future, we will need to make sure that we can never run into
            problems with out-of-date metadata being returned.

            """
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

        def __repr__(self):
            return "Reader({}: {})".format(self.datatype.full_datatype_name(), self.base_dir)

    class Writer:
        """
        The abstract superclass of all dataset writers.

        You do not need to subclass or instantiate these yourself: subclasses are created automatically
        to correspond to each datatype. You can add functionality to a datatype's writer by creating a
        nested `Writer` class. This will inherit from the parent datatype's writer. This happens
        automatically - you don't need to do it yourself and shouldn't inherit from anything:

        .. code-block:: py
           class MyDatatype(PimlicoDatatype):
               class Writer:
                   # Overide writer things here

        Writers should be used as context managers. Typically, you will get hold of a writer
        for a module's output directly from the module-info instance:

        .. code-block:: py

           with module.get_output_writer("output_name") as writer:
               # Call the writer's methods, set its attributes, etc
               writer.do_something(my_data)
               writer.some_attr = "This data"

        Any additional kwargs passed into the writer (which you can do by passing kwargs to
        ``get_output_writer()`` on the module) will set values in the dataset's metadata.
        Available parameters are given, along with their default values, in the dictionary
        ``metadata_defaults`` on a Writer class. They also include all values from ancestor
        writers.

        It is important to pass in parameters as kwargs that affect the writing of the data,
        to ensure that the correct values are available as soon as the writing process starts.

        All metadata values, including those passed in as kwargs, should be serializable
        as simple JSON types.

        Another set of parameters, *writer params*, is used to specify things that affect
        the writing process, but do not need to be stored in the metadata. This could be,
        for example, the number of CPUs to use for some part of the writing process. Unlike,
        for example, the format of the stored data, this is not needed later when the data
        is read.

        Available writer params are given, along with their default values, in the dictionary
        ``writer_param_defaults`` on a Writer class. (They do not need to be JSON serializable.)
        Their values are also specified as kwargs in the same way as metadata.

        """
        # Values should be (val, doc) pairs, where val is the default value and doc is a string describing
        # what the parameter is for (used for documentation)
        metadata_defaults = {}
        writer_param_defaults = {}

        def __init__(self, datatype, base_dir, pipeline, module=None, **kwargs):
            self.datatype = datatype
            self.pipeline = pipeline
            self.module = module

            self.base_dir = base_dir
            # This is the directory all data should be written to
            self.data_dir = self.datatype._get_data_dir(base_dir)
            self._metadata_path = os.path.join(self.base_dir, "corpus_metadata")

            # Corpus metadata that will be written out to a JSON file accompanying the dataset
            # Values can be set using kwargs, but typically the metadata should not be modified
            #  by the user once the context manager is entered, as the writing process may be
            #  parameterized by these values
            self.metadata = {}

            # Extract kwargs that correspond to metadata keys
            for key, default in self.metadata_defaults.items():
                if key in kwargs:
                    self._metadata[key] = kwargs.pop(key)
                else:
                    self._metadata[key] = default
            # Check here that metadata from kwargs is all JSON serializable, to avoid mysterious errors later
            try:
                json.dumps(self._metadata)
            except TypeError, e:
                raise DatatypeWriteError(
                    "metadata parameters passed to writer as kwargs must be JSON serializable: {}".format(e)
                )

            # Extract kwargs that correspond to writer params
            self.params = {}
            for key, default in self.writer_param_defaults.items():
                if key in kwargs:
                    self.params[key] = kwargs.pop(key)
                else:
                    self.params[key] = default

            # Any remaining kwargs are incorrect, as they're not listed as either metadata or writer param keys
            if len(kwargs):
                raise DatatypeWriteError("writer kwargs not valid as metadata keys or writer parameters: {}".format(
                    ", ".join(kwargs.keys())
                ))

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
            """ Mark the named task as completed """
            if task in self._to_output:
                self._to_output.remove(task)

        @property
        def incomplete_tasks(self):
            """ List of required tasks that have not yet been completed """
            return list(self._to_output)

        def __enter__(self):
            # Make sure the necessary directories exist
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
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
            with open(self._metadata_path, "w") as f:
                # We used to pickle the metadata dictionary, but now we store it as JSON, so it's readable
                json.dump(self.metadata, f)
                # Make sure that the file doesn't get buffered anywhere, but is fully written to disk now
                # We need to be sure that the up-to-date metadata is available immediately
                f.flush()
                os.fsync(f.fileno())

        def __repr__(self):
            return "Writer({}: {})".format(self.datatype.full_datatype_name(), self.base_dir)


    ########## Type hiearchy construction for readers and writers ###########
    # Readers and writers are in a type hierarchy that exactly mirrors the datatype hierarchy.
    # Methods are added and overridden according to the specifications of the Reader and Writer dummy classes

    @classmethod
    def _get_reader_cls(cls):
        if cls is PimlicoDatatype:
            # On the base class, we just return the base reader, subclassing object
            parent_reader = object
        else:
            # In case of multiple inheritance, first base class is the one we use to inherit reader functionality
            # Typically multiple inheritance probably won't be used anyway with datatypes
            parent_reader = cls.__bases__[0]._get_reader_cls()

        my_reader = cls.Reader
        if parent_reader is my_reader:
            # Reader is not overridden, so we don't need to subclass
            return parent_reader
        else:
            # Perform subclassing so that a new Reader is created that is a subclass of the parent's reader
            return type("{}Reader".format(cls.__name__), (parent_reader,), my_reader.__dict__)

    @classmethod
    def _get_some_writer_cls(cls):
        """ Get writer subclass, even if this type has no writer, going up the type hierarchy if necessary """
        if cls is PimlicoDatatype:
            # On the base class, parent is just object
            parent_writer = object
        else:
            # In case of multiple inheritance, first base class is the one we use to inherit writer functionality
            parent_writer = cls.__bases__[0]._get_some_writer_cls()

        my_writer = cls.Writer
        if my_writer is None:
            # No writer for this type, but we want to get some writer
            # Go up type hieararchy, skipping types for which Writer is None
            return parent_writer
        elif parent_writer is my_writer:
            # Writer is not overridden, so we don't need to subclass
            return parent_writer
        else:
            new_cls_dict = dict(my_writer.__dict__)
            new_metadata_defaults = new_cls_dict.get("metadata_defaults", {})
            new_writer_param_defaults = new_cls_dict.get("writer_param_defaults", {})
            # Collect metadata_defaults and writer params from the Writer if given
            new_cls_dict["metadata_defaults"] = dict(parent_writer.metadata_defaults, **new_metadata_defaults)
            new_cls_dict["writer_param_defaults"] = dict(parent_writer.writer_param_defaults, **new_writer_param_defaults)

            # Check that defaults were given in the right format
            for val in new_metadata_defaults.values():
                if type(val) not in (list, tuple) or len(val) != 2:
                    raise TypeError("writer metadata defaults should be pairs of default values and documentation "
                                    "strings: invalid dictionary for {} writer".format(cls.datatype_name))
            for val in new_writer_param_defaults.values():
                if type(val) not in (list, tuple) or len(val) != 2:
                    raise TypeError("writer param defaults should be pairs of default values and documentation "
                                    "strings: invalid dictionary for {} writer".format(cls.datatype_name))

            # Perform subclassing so that a new Writer is created that is a subclass of the parent's writer
            return type("{}Writer".format(cls.__name__), (parent_writer,), new_cls_dict)

    @classmethod
    def _get_writer_cls(cls):
        """ Get the writer subclass, or None if this type has no writer """
        my_writer = cls.Writer
        if my_writer is None:
            # This datatype has been marked as not having a writer
            # In this case, we return None, indicating that no writer is avialable
            return None
        else:
            # Hand over the the subtyping routine that skips over Nones to construct the writer type
            return cls._get_some_writer_cls()


class DynamicOutputDatatype(object):
    """
    Types of module outputs may be specified as an instance of a subclass of
    :class:`.PimlicoDatatype`, or alternatively
    as an instance of DynamicOutputType. In this case, get_datatype() is called when the output datatype is
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
    Types of module inputs may be given as an instance of a subclass of
    :class:`.PimlicoDatatype`, a tuple of datatypes, or
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
    
    In a config file, if you need the same input specification to be repeated multiple times in a list,
    instead of writing it out explicitly you can use a multiplier to repeat it N times by putting
    ``*N`` after it. This is particularly useful when ``N`` is the result of expanding module variables,
    allowing the number of times an input is repeated to depend on some modvar expression.

    When get_input() is called on the module, instead of returning a single datatype, a list of datatypes is returned.

    """
    def __init__(self, datatype_requirements):
        self.datatype_requirements = datatype_requirements


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


class DataNotReadyError(Exception):
    pass


def load_datatype(path, options={}):
    """
    Try loading a datatype class for a given path. Raises a DatatypeLoadError if it's not a valid
    datatype path.

    Options are unprocessed strings that will be processed using the datatype's option
    definitions.

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

    # Instantiate the datatype, taking account of (unprocessed) options
    dt = cls.instantiate_from_options(options)

    return dt
