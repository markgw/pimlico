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

from pimlico.core.modules.options import process_module_options
from pimlico.utils.core import import_member, cached_property

__all__ = [
    "PimlicoDatatype",
    "DynamicOutputDatatype", "DynamicInputDatatypeRequirement",
    "DatatypeLoadError", "DatatypeWriteError",
    "load_datatype", "MultipleInputs",
]


_class_name_word_boundary = re.compile(r"([a-z])([A-Z])")


class PimlicoDatatypeMeta(type):
    """
    Metaclass for all Pimlico datatype classes. Takes care of preparing a Reader and
    Writer class for every datatype.

    You should never need to do anything with this: it's used by the base datatype,
    and hence by every other datatype.

    """
    def __new__(cls, *args, **kwargs):
        new_cls = super(PimlicoDatatypeMeta, cls).__new__(cls, *args, **kwargs)
        # Replace the existing Reader class, if any, which is used to construct the actual Reader,
        # with the constructed Reader
        new_cls.Reader = PimlicoDatatypeMeta._get_reader_cls(new_cls)
        # Do the same with the Writer
        new_cls.Writer = PimlicoDatatypeMeta._get_writer_cls(new_cls)
        # Also prepare a Writer to inherit from, even if this class' writer should be None
        new_cls._NotNoneWriter = PimlicoDatatypeMeta._get_some_writer_cls(new_cls)

        return new_cls

    ########## Type hiearchy construction for readers and writers ###########
    # Readers and writers are in a type hierarchy that exactly mirrors the datatype hierarchy.
    # Methods are added and overridden according to the specifications of the Reader and Writer dummy classes

    @staticmethod
    def _get_reader_cls(cls):
        # Use a special attribute that includes the class name to cache the reader so that we only
        # cache for this exact type and don't inherit
        # This is like Python's mangling of "__" names, but we can't use that because it happens at
        # compile time, so all of these would use PimlicoDatatype for mangling
        _cache_name = "_{}_reader_cls".format(cls.__name__)

        if not hasattr(cls, _cache_name):
            # Fetch the reader type
            if len(cls.__bases__) == 0 or cls.__bases__[0] is object:
                # On the base class, we just return the base reader, subclassing object
                parent_reader = object
            else:
                # In case of multiple inheritance, first base class is the one we use to inherit reader functionality
                # Typically multiple inheritance probably won't be used anyway with datatypes
                parent_reader = cls.__bases__[0].Reader

            my_reader = cls.Reader
            if parent_reader is my_reader:
                # Reader is not overridden, so we don't need to subclass
                reader_cls = parent_reader
            else:
                # Perform subclassing so that a new Reader is created that is a subclass of the parent's reader
                my_dict = dict(my_reader.__dict__)
                # Don't inherit the cached setup cls for this reader type, as we should recompute to do subtyping
                if "_setup_cls" in my_dict:
                    del my_dict["_setup_cls"]
                reader_cls = PimlicoDatatypeReaderMeta("{}Reader".format(cls.__name__), (parent_reader,), my_dict)
            setattr(cls, _cache_name, reader_cls)

        return getattr(cls, _cache_name)

    @staticmethod
    def _get_some_writer_cls(cls):
        """ Get writer subclass, even if this type has no writer, going up the type hierarchy if necessary """
        # Clever cacheing: see _get_reader_cls()
        _cache_name = "_{}_writer_cls".format(cls.__name__)

        if not hasattr(cls, _cache_name):
            if len(cls.__bases__) == 0 or cls.__bases__[0] is object:
                # On the base class, parent is just object
                parent_writer = object
            else:
                # In case of multiple inheritance, first base class is the one we use to inherit writer functionality
                parent_writer = cls.__bases__[0]._NotNoneWriter

            my_writer = cls.Writer
            if my_writer is None:
                # No writer for this type, but we want to get some writer
                # Go up type hieararchy, skipping types for which Writer is None
                writer_cls = parent_writer
            elif parent_writer is my_writer:
                # Writer is not overridden, so we don't need to subclass
                writer_cls = parent_writer
            else:
                new_cls_dict = dict(my_writer.__dict__)
                if parent_writer is not object:
                    new_metadata_defaults = new_cls_dict.get("metadata_defaults", {})
                    new_writer_param_defaults = new_cls_dict.get("writer_param_defaults", {})
                    # Collect metadata_defaults and writer params from the Writer if given
                    new_cls_dict["metadata_defaults"] = dict(parent_writer.metadata_defaults,
                                                             **new_metadata_defaults)
                    new_cls_dict["writer_param_defaults"] = dict(parent_writer.writer_param_defaults,
                                                                 **new_writer_param_defaults)

                    # Check that defaults were given in the right format
                    for val in new_metadata_defaults.values():
                        if type(val) not in (list, tuple) or len(val) != 2:
                            raise TypeError(
                                "writer metadata defaults should be pairs of default values and documentation "
                                "strings: invalid dictionary for {} writer".format(cls.datatype_name))
                    for val in new_writer_param_defaults.values():
                        if type(val) not in (list, tuple) or len(val) != 2:
                            raise TypeError(
                                "writer param defaults should be pairs of default values and documentation "
                                "strings: invalid dictionary for {} writer".format(cls.datatype_name))

                # Perform subclassing so that a new Writer is created that is a subclass of the parent's writer
                writer_cls = type("{}Writer".format(cls.__name__), (parent_writer,), new_cls_dict)
            setattr(cls, _cache_name, writer_cls)
        return getattr(cls, _cache_name)

    @staticmethod
    def _get_writer_cls(cls):
        """ Get the writer subclass, or None if this type has no writer """
        my_writer = cls.Writer
        if my_writer is None:
            # This datatype has been marked as not having a writer
            # In this case, we return None, indicating that no writer is avialable
            return None
        else:
            # Hand over the the subtyping routine that skips over Nones to construct the writer type
            return PimlicoDatatypeMeta._get_some_writer_cls(cls)


class PimlicoDatatypeReaderMeta(type):
    """
    Metaclass for all Pimlico readers, which are (mostly) created automatically, one
    for each datatype.

    This metaclass takes case of creating a Setup class to correspond to each Reader
    class.

    """
    def __new__(cls, *args, **kwargs):
        new_cls = super(PimlicoDatatypeReaderMeta, cls).__new__(cls, *args, **kwargs)
        # Replace the existing Setup class, if any, which is used to construct the actual Setup,
        # with the constructed Seupt
        new_cls.Setup = PimlicoDatatypeReaderMeta._get_setup_cls(new_cls)
        return new_cls

    @staticmethod
    def _get_setup_cls(cls):
        # Cache the setup cls for the reader type
        # Clever cacheing: see _get_reader_cls()
        # Use the class' ID, in case the reader type names aren't unique
        _cache_name = "_{}_setup_cls".format(id(cls))
        if not hasattr(cls, _cache_name):
            if len(cls.__bases__) == 0 or cls.__bases__[0] is object:
                # On the base class, we just return the base setup, subclassing object
                parent_setup = object
            else:
                # In case of multiple inheritance, first base class is the one we use to inherit setup functionality
                parent_setup = cls.__bases__[0].Setup

            my_setup = cls.Setup
            if my_setup is parent_setup:
                # Setup is not overridden, so we don't need to subclass
                setup_cls = parent_setup
            else:
                # Perform subclassing so that a new Setup is created that is a subclass of the parent's setup
                my_dict = dict(my_setup.__dict__)
                my_dict["reader_type"] = cls
                setup_cls = type("{}Setup".format(cls.__name__), (parent_setup,), my_dict)
            setattr(cls, _cache_name, setup_cls)
        return getattr(cls, _cache_name)


class PimlicoDatatype(object):
    __metaclass__ = PimlicoDatatypeMeta
    """
    The abstract superclass of all datatypes. Provides basic functionality for identifying where
    data should be stored and such.

    Datatypes are used to specify the routines for reading the output from modules, via their reader
    class.

    `module` is the ModuleInfo instance for the pipeline module that this datatype was produced by. It may
    be None, if the datatype wasn't instantiated by a module. It is not required to be set if you're
    instantiating a datatype in some context other than module output. It should generally be set for
    input datatypes, though, since they are treated as being created by a special input module.

    Creating a new datatype
    =======================

    This is the typical process for creating a new datatype. Of course, some datatypes do more and
    some of the following is not always necessary, but it's a good guide for reference.

    1. Create the datatype class, which may subclass :class:`PimlicoDatatype` or some other existing
       datatype.
    2. Specify a `datatype_name` as a class attribute.
    3. Specify software dependencies for reading the data, if any, by overriding `get_software_dependencies()`
       (calling the super method as well).
    4. Specify software dependencies for writing the data, if any that are not among the reading dependencies,
       by overriding `get_writer_software_dependencies()`
    5. Define a nested `Reader` class to add any methods to the reader for this datatype. The data should
       be read from the directory given by its `data_dir`. It should provide methods for getting different
       bits of the data, iterating over it, or whatever is appropriate.
    6. Define a nested `Setup` class within the reader with a `data_ready(base_dir)` method to check whether the
       data in `base_dir` is ready to be read using the reader.
       If all that this does is check the existence of particular filenames or paths within the data
       dir, you can instead implement the `Setup` class' `get_required_paths()` method to return the
       paths relative to the data dir.
    7. Define a nested `Writer` class in the datatype to add any methods to the writer for this datatype.
       The data should be written to the path given by its `data_dir`. Provide methods that the user can
       call to write things to the dataset. Required elements of the dataset should be specified as a list of
       strings as the `required_tasks` attribute and ticked off as written using `task_complete()`
    8. You may want to specify:

       * `datatype_options`: an OrderedDict of option definitions
       * `shell_commands`: a list of shell commands associated with the datatype

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

    def __call__(self, *args, **kwargs):
        """
        Instantiate a reader setup of the relevant type. Args and kwargs will be
        passed through to the setup class' init. They may depend on the particular
        setup class, but typically one arg is required, which is a list of paths
        where the data may be found.

        You can use the reader setup to get a reader, once the data is ready to
        read.

        .. code-block:: py

           datatype = ThisDatatype(options...)
           # Most of the time, you will pass in a list of possible paths to the data
           setup = datatype(possible_paths_list)
           reader = setup.get_reader(pipeline, module="pipeline_module")

        """
        # Get the standard reader class for this datatype
        # Get the reader type's corresponding setup class and instantiate it
        return self.Reader.get_setup(self, *args, **kwargs)

    def get_writer(self, base_dir, pipeline, module=None, **kwargs):
        """
        Instantiate a writer to write data to the given base dir.

        Kwargs are passed through to the writer and used to specify initial metadata and
        writer params.

        :param base_dir: output dir to write dataset to
        :param pipeline: current pipeline
        :param module: module name (optional, for debugging only)
        :return: instance of the writer subclass corresponding to this datatype
        """
        # Get the writer class
        writer_cls = self.Writer
        if writer_cls is None:
            raise DatatypeWriteError("datatype {} does not provide writing functionality".format(self.datatype_name))
        return writer_cls(self, base_dir, pipeline, module=module, **kwargs)

    @classmethod
    def instantiate_from_options(cls, options={}):
        """Given string options e.g. from a config file, perform option processing and instantiate datatype"""
        options = process_module_options(cls.datatype_options, options, "{} dataset loader".format(cls.datatype_name))
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
                   # Override reader things here

        """
        def __init__(self, datatype, setup, pipeline, module=None):
            self.datatype = datatype
            self.pipeline = pipeline
            self.module = module
            self.setup = setup

            self.process_setup()

        def process_setup(self):
            """
            Do any processing of the setup object (e.g. retrieving values and setting
            attributes on the reader) that should be done when the reader is instantiated.

            """
            self.base_dir = self.setup.get_base_dir()
            self.data_dir = self.setup.get_data_dir()

        def get_detailed_status(self):
            """
            Returns a list of strings, containing detailed information about the data.

            Subclasses may override this to supply useful (human-readable) information specific to the datatype.
            They should called the super method.

            """
            return []

        class Setup:
            """
            Abstract superclass of all dataset reader setup classes.

            These classes provide any functionality relating to a reader needed before it is
            ready to read and instantiated. Most importantly, it provides the `ready_to_read()`
            method, which indicates whether the reader is ready to be instantiated.

            The standard implementation, which can be used in almost all cases,
            takes a list of possible paths to the dataset at initialization and checks
            whether the dataset is ready to be read from any of them. You generally
            don't need to override `ready_to_read()` with this, but just
            `data_ready()`, which checks whether the data is ready to be read in a
            specific location. You can call the parent class' data-ready checks
            using super: `super(MyDatatype.Reader.Setup, self).data_ready()`.

            The whole `Setup` object will
            be passed to the corresponding `Reader`'s init, so that it has access to
            data locations, etc.

            Subclasses may take different init args/kwargs and store whatever attributes
            are relevant for preparing their corresponding `Reader`. In such cases, you
            will usually override a `ModuleInfo`'s `get_output_reader_setup()` method
            for a specific output's reader preparation, to provide it with the appropriate
            arguments. Do this by calling the `Reader` class' `get_setup(*args, **kwargs)`
            class method, which passes args and kwargs through to the `Setup`'s init.

            You do not need to subclass or instantiate these yourself: subclasses are created automatically
            to correspond to each reader type. You can add functionality to a reader's setup by creating a
            nested `Setup` class. This will inherit from the parent reader's setup. This happens
            automatically - you don't need to do it yourself and shouldn't inherit from anything:

            .. code-block:: py
               class MyDatatype(PimlicoDatatype):
                   class Reader:
                       # Overide reader things here

                       class Setup:
                           # Override setup things here
                           # E.g.:
                           def data_ready(path):
                               # Parent checks: usually you want to do this
                               if not super(MyDatatype.Reader.Setup, self).data_ready(path):
                                  return False
                               # Check whether the data's ready according to our own criteria
                               # ...
                               return True

            The first arg to the init should always be the datatype instance.

            """
            reader_type = None

            def __init__(self, datatype, data_paths):
                self.datatype = datatype
                self.data_paths = data_paths

            def data_ready(self, path):
                """
                Check whether the data at the given path is ready to be read using
                this type of reader. It may be called several times with different
                possible base dirs to check whether data is available at any of them.

                Often you will override this for particular datatypes to provide special
                checks. You may (but don't have to) check the setup's parent implementation
                of `data_ready()` by calling
                `super(MyDatatype.Reader.Setup, self).data_ready(path)`.

                The base implementation just checks whether the data dir exists.
                Subclasses will typically want to add their own checks.

                """
                # Check the data dir is also there
                if not os.path.exists(path):
                    return False
                data_dir = _get_data_dir(path)
                if not os.path.exists(data_dir):
                    return False

                # Check whether any additional paths exist
                paths = self.get_required_paths()
                if paths:
                    for path in paths:
                        if os.path.isabs(path):
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

            def ready_to_read(self):
                """
                Check whether we're ready to instantiate a reader using this setup. Always
                called before a reader is instantiated.

                Subclasses may override this, but most of the time you won't need to. See
                `data_ready()` instead.

                :return: True if the reader's ready to be instantiated, False otherwise
                """
                return any(self._paths_ready)

            def get_required_paths(self):
                """
                May be overridden by subclasses to provide a list of paths (absolute, or
                relative to the data dir) that must exist for the data to be considered
                ready.

                """
                return []

            def get_base_dir(self):
                """
                :return: the first of the possible base dir paths at which the data is
                ready to read. Raises an exception if none is ready. Typically used to
                get the path from the reader, once we've already confirmed that at least
                one is available.

                """
                try:
                    return (path for (path, ready) in zip(self.data_paths, self._paths_ready) if ready).next()
                except StopIteration:
                    raise DataNotReadyError("tried to get base dir from reader setup, but no path provides ready data")

            def get_data_dir(self):
                """
                :return: the path to the data dir within the base dir (typically a dir called "data")
                """
                return _get_data_dir(self.get_base_dir())

            def read_metadata(self, base_dir):
                """
                Read in metadata for a dataset stored at the given path. Used by
                readers and rarely needed outside them. It may sometimes be necessary
                to call this from `data_ready()` to check that required metadata is
                available.

                """
                if os.path.exists(_metadata_path(base_dir)):
                    # Load dictionary of metadata
                    with open(_metadata_path(base_dir), "r") as f:
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

            def __call__(self, pipeline, module=None):
                """
                Instantiate a reader using this setup.
                Alias for `get_reader()`

                """
                return self.get_reader(pipeline, module=module)

            def get_reader(self, pipeline, module=None):
                """
                Instantiate a reader using this setup.

                :param pipeline: currently loaded pipeline
                :param module: (optional) module name of the module by which the datatype has been
                    loaded. Used for producing intelligible error output
                """
                return self.reader_type(self.datatype, self, pipeline, module=module)

            @cached_property
            def _paths_ready(self):
                return [self.data_ready(path) for path in self.data_paths]

            def __repr__(self):
                return "{}()".format(self.__class__.__name__)

            def _get_data_dir(self, base_dir):
                return _get_data_dir(base_dir)

        @classmethod
        def get_setup(cls, datatype, *args, **kwargs):
            """
            Instantiate a reader setup object for this reader. The args and kwargs are those
            of the reader's corresponding setup class and will be passed straight through
            to the init.

            """
            return cls.Setup(datatype, *args, **kwargs)

        def _get_metadata(self):
            """
            Read in metadata from a file in the corpus directory.

            Note that this is no longer cached in memory. We need to be sure that the metadata values returned are
            always up to date with what is on disk, so always re-read the file when we need to get a value from
            the metadata. Since the file is typically small, this is unlikely to cause a problem. If we decide to
            return to cacheing the metadata dictionary in future, we will need to make sure that we can never run into
            problems with out-of-date metadata being returned.

            """
            return self.setup.read_metadata(self.setup.get_base_dir())
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
        #: This can be overriden on writer classes to add this list of tasks to the required tasks when the
        #: writer is initialized
        required_tasks = []

        def __init__(self, datatype, base_dir, pipeline, module=None, **kwargs):
            self.datatype = datatype
            self.pipeline = pipeline
            self.module = module

            self.base_dir = base_dir
            # This is the directory all data should be written to
            self.data_dir = _get_data_dir(base_dir)
            self._metadata_path = os.path.join(self.base_dir, "corpus_metadata")

            # Corpus metadata that will be written out to a JSON file accompanying the dataset
            # Values can be set using kwargs, but typically the metadata should not be modified
            #  by the user once the context manager is entered, as the writing process may be
            #  parameterized by these values
            self.metadata = {}

            # Extract kwargs that correspond to metadata keys
            for key, (default, doc) in self.metadata_defaults.items():
                if key in kwargs:
                    self.metadata[key] = kwargs.pop(key)
                else:
                    self.metadata[key] = default
            # Check here that metadata from kwargs is all JSON serializable, to avoid mysterious errors later
            try:
                json.dumps(self.metadata)
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

            # Set any required tasks that were specified as a class attribute
            if len(self.required_tasks):
                self.require_tasks(*self.required_tasks)

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


def _get_data_dir(base_dir):
    return os.path.join(base_dir, "data")


def _metadata_path(base_dir):
    return os.path.join(base_dir, "corpus_metadata")


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

    # The type of the class will generally not be "type", since we use meta classes
    # However, it should be a subclass of it
    # This distinguishes it from, e.g. modules
    if not issubclass(type(cls), type(object)):
        raise DatatypeLoadError("tried to load datatype %s, but result was not a class, it was a %s" %
                                (path, type(cls).__name__))

    if not issubclass(cls, PimlicoDatatype):
        raise DatatypeLoadError("%s is not a Pimlico datatype" % path)

    # Instantiate the datatype, taking account of (unprocessed) options
    dt = cls.instantiate_from_options(options)

    return dt
