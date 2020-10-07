# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Base classes and utilities for input modules in a pipeline.

"""
from builtins import next
from builtins import object
import types

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.core.modules.map import output_to_document
from pimlico.datatypes import PimlicoDatatype, GroupedCorpus
from pimlico.datatypes.base import PimlicoDatatypeReaderMeta
from pimlico.datatypes.corpora import IterableCorpus
from pimlico.modules.corpora.group.info import CorpusGroupReader, ModuleInfo as GrouperModuleInfo

from .base import BaseModuleInfo
from future.utils import with_metaclass


class InputReader(with_metaclass(PimlicoDatatypeReaderMeta, PimlicoDatatype.Reader)):
    """
    Special base class for readers that read in input data to provide access to
    it through an input reader module.

    You might sometimes want to override this yourself, but most often you'll
    use the :func:`iterable_input_reader` factory function.

    """

    def iterate(self):
        """ Should be overridden """
        raise NotImplementedError("input reader did not override iterate()")

    def __init__(self, *args, **kwargs):
        super(InputReader, self).__init__(*args, **kwargs)
        # Provide easy access to the options from the config
        self.options = self.setup.reader_options

    class Setup(object):
        execute_count = False
        # If True, the reader will not be ready to read until its length has been stored

        def check_data_ready(self):
            """ Should be overridden to use self.reader_options to check whether the data is ready to read """
            raise NotImplementedError("input reader did not override check_data_ready()")

        def count(self):
            """ Should be overridden in all cases """
            raise NotImplementedError("input reader did not override count()")

        def __init__(self, datatype, output_dir, reader_options):
            self.datatype = datatype
            self.reader_options = reader_options
            self.output_dir = output_dir

        def ready_to_read(self):
            # If executing a count, make sure the result is ready before we read the data
            if self.execute_count and self.read_metadata(self.output_dir).get("length", None) is None:
                return False
            return self.check_data_ready()

    def __len__(self):
        if "length" in self.metadata:
            # If the length has been stored, use that
            return self.metadata["length"]
        else:
            return self.setup.count()

    def __iter__(self):
        # Check that the first document is of the right type
        # There's no need to check all the documents, but it's worth checking one in case the user
        # of the factory function has made a mistake in building the iter_fn
        it = iter(self.iterate())
        doc_name, doc = next(it)
        dp_type = self.datatype.data_point_type
        # Like process_document() on doc map modules, we allow raw data or dicts to be returned
        doc = output_to_document(doc, dp_type)
        if not self.datatype.data_point_type.is_type_for_doc(doc):
            raise TypeError("data iterator for input reader yielded the wrong type of document. Expected "
                            "a document of data point type {}, but got {}".format(
                self.datatype.data_point_type, type(doc).__name__
            ))
        # Yield this first document and don't check any others
        yield doc_name, doc
        # Just iterate over the rest
        for doc_name, doc in it:
            doc = output_to_document(doc, dp_type)
            yield doc_name, doc

    def process_setup(self):
        """ Override so we don't try to get base_dir, etc, as the standard reader does """
        return

    def _get_metadata(self):
        if self.setup.execute_count:
            return self.setup.read_metadata(self.setup.output_dir)
        else:
            return {}

    metadata = property(_get_metadata)


class InputModuleInfo(BaseModuleInfo):
    """
    Base class for input modules. These don't get executed in general,
    they just provide a way to iterate over input data.

    You probably don't want to subclass this. You can create a subclass
    more simply by using the factory :func:`iterable_input_reader`.

    Subclassing this ModuleInfo is another way to create an input
    reader module, which is in some cases more flexible, for example
    for allowing a module info to be overridden to create related
    readers. In this case, you should make sure to override the following:

    * `module_type_name`
    * `module_readable_name`
    * `input_reader_class` to the Reader subclass that should be used
      for reading the data, a subclass of :class:`InputReader`
    * `module_outputs` should have exactly one output, with the appropriate
      datatype that is supplied by the reader

    You might also want to override:

    * `module_executable` if the module is to be executed before the data
      can be read
    * `module_executor_override` if the module is executable. No executor
      will be found if this is not set. Most often, it is set to
      :class:`DocumentCounterModuleExecutor`, as it is by the factory
    * `get_software_dependencies`

    Note that `module_executable` is typically set to False and the base
    class does this. However, some input modules need to be executed
    before the input is usable, for example to collect stats about the
    input data. The most common example of this is if `execute_count`
    is set when calling the factory.

    """
    module_type_name = "input"
    module_readable_name = "unnamed input module"
    module_executable = False
    input_reader_class = None
    # Should be overridden to point to the InputReader subclass to use to read the data
    grouped = True
    # By default, the produced output is a GroupedCorpus.
    # Set this to False to skip grouping and produce an IterableCorpus
    # You also need to add the grouper module info's options to the module options (see how the factory does it)

    def instantiate_output_reader_setup(self, output_name, datatype):
        input_module_options = dict(self.module_options)

        if not self.grouped:
            reader_option_keys = list(input_module_options.keys())
            grouper_option_keys = []
        else:
            # Keep track of what keys have been added for the grouper, so we can separate out the values
            grouper_option_keys = list(GrouperModuleInfo.module_options.keys())
            reader_option_keys = [k for k in input_module_options.keys() if k not in grouper_option_keys]

        reader_options = dict((key, v) for (key, v) in self.options.items() if key in reader_option_keys)
        input_reader_setup = self.input_reader_class.Setup(datatype,
                                                           self.get_absolute_output_dir(output_name), reader_options)
        if not self.grouped:
            # Not grouping into a GroupedCorpus: just use the InputReader directly
            return input_reader_setup
        else:
            # Use the input reader to read documents, but pass through CorpusGroupReader as well
            grouper_options = dict((key, v) for (key, v) in self.options.items() if key in grouper_option_keys)
            return CorpusGroupReader.Setup(datatype, input_reader_setup, grouper_options)

    def missing_module_data(self):
        # This is called to check whether the module is ready to run
        # In the case of a count executor, as well as checking that the input
        # data is ready before we supply it at the output, we also have to
        # check that it's ready (except the count) before running

        missing_data = []
        if self.module_executable:
            # Get a reader setup for the output
            output_setup = self.get_output_reader_setup()
            # If the setup is wrapped in a grouper setup, get the wrapped setup
            if self.grouped:
                output_setup = output_setup.input_reader_setup

            # Check whether the data is ready to read, aside from input preparation
            if not output_setup.check_data_ready():
                missing_data.append("Input module's source data not ready")
        return missing_data


class DocumentCounterModuleExecutor(BaseModuleExecutor):
    """
    An executor that just calls the len method to count documents and stores the result

    """
    def execute(self):
        # The count() function is supplied by the output reader setup
        # We can't instantiate the reader yet, as the count isn't done!
        output_setup = self.info.get_output_reader_setup()
        # If the setup is wrapped in a grouper setup, get the wrapped setup
        if self.info.grouped:
            output_setup = output_setup.input_reader_setup

        self.log.info("Counting documents in corpus")
        num_docs = output_setup.count()
        num_valid_docs = None

        if type(num_docs) is tuple:
            # A pair of values was returned: this is the num docs and num valid docs
            if len(num_docs) > 2:
                raise ModuleExecutionError(
                    "document counter for input corpus returned a tuple with {} values. Expected either "
                    "one or two values (num docs and num valid docs)".format(len(num_docs))
                )
            elif len(num_docs) == 1:
                num_docs = num_docs[0]
            else:
                num_docs, num_valid_docs = num_docs

        self.log.info("Corpus contains {:,} docs. Storing count".format(num_docs))
        output_datatype = output_setup.datatype
        # Don't use get_output_writer here, as we're not actually writing out a corpus
        # GroupedCorpus has a writer than writes documents and handles the corpus length in its own way
        # Here we create a simple PimlicoDatatype.Writer ourselves and set the metadata manually
        with PimlicoDatatype.Writer(
                output_datatype, self.info.get_absolute_output_dir("corpus"),
                self.info.pipeline, self.info.module_name) as writer:
            # Set any default metadata values for the correct output datatype
            writer.metadata.update(
                dict((key, spec[0]) for (key, spec) in output_datatype.Writer.metadata_defaults.items())
            )
            writer.metadata["length"] = num_docs
            if num_valid_docs is not None:
                writer.metadata["valid_documents"] = num_valid_docs


def input_module_factory(datatype):
    """
    Create an input module class to load a given datatype.

    This is used by the pipeline config loader to create a suitable module type
    when the config has a datatype as a module type. It loads data from the
    given directory exactly as if Pimlico had itself output a dataset of the
    specified type to that directory.

    The main use for this is loading prepared datasets in test pipelines. It
    is also useful if you have output from some other Pimlico pipeline that
    you just want to load as it is and use as input to a module.

    It is not for loading input data from external sources. See `iterable_input_reader`
    for creating normal input modules.

    """
    class DatatypeInputModuleInfo(InputModuleInfo):
        module_type_name = "%s_input" % datatype.datatype_name
        module_readable_name = "%s datatype input" % datatype.datatype_name
        module_outputs = [("data", datatype)]
        # One special option to allow a dir to be specified to read the data from
        # This will become the base_dir for the datatype when instantiated
        module_options = {
            "dir": {
                "help": "Directory to read the data from. May be used to load a dataset from an output from another "
                        "Pimlico pipeline",
                "required": True,
            },
        }
        # Set module to support Python 2, since it doesn't do anything
        # If the datatype doesn't support Python 2, this will get checked anyway
        module_supports_python2 = True

        def instantiate_output_reader_setup(self, output_name, datatype):
            # Create a reader setup that just has the given directory as a possible location for the data
            return datatype([self.options["dir"]])

    return DatatypeInputModuleInfo


def iterable_input_reader(input_module_options, data_point_type,
                          data_ready_fn, len_fn=None, iter_fn=None,
                          module_type_name=None, module_readable_name=None,
                          software_dependencies=None, execute_count=False, no_group=False, python2=False):
    """
    Factory for creating an input reader module info.
    This is a (typically) non-executable module that has no
    inputs. It reads its data from some external location,
    using the given module options. The resulting
    dataset is a GroupedCorpus, with the given document type.

    This is the normal way to create input reader modules.

    The returned class is a subclass of :class:`~pimlico.core.modules.base.BaseModuleInfo`.
    It is typically used like this, within a Pimlico module's `info.py`:

    .. code-block:: py

       ModuleInfo = iterable_input_reader(
           {
               # ... module options ...
           },
           DataPointType(),
           data_ready_function,
           len_function,
           iter_function,
           "my_module_name"
       )

    If `execute_count=True`, the module will be an executable module and the execution will simply count
    the number of documents in the corpus and store the count. This should be used if counting the documents
    in the dataset is not completely trivial and quick (e.g. if you need to read through the data itself,
    rather than something like counting files in a directory or checking metedata).
    It is common for this to be the only processing that needs to be done on the dataset before using it.
    The len_fn is used to count the documents in the module's execution phase.

    If the counting method returns a pair of integers, instead of just a single integer,
    they are taken to be the total number of documents in the corpus and the number of valid documents
    (i.e. the number that will be produce an InvalidDocument). In this case, the valid documents count
    is also stored in the metadata, as ``valid_documents``.

    Reader options are available at read time from the reader setup instance's ``reader_options`` attribute,
    also available from the reader instance as ``reader.options``.

    .. note::

       Producing an IterableCorpus used to be the default behaviour. However, since we almost
       always want to convert to a GroupedCorpus immediately after reading, the default behaviour
       is now to do the grouping as part of the reading process and produce a GroupedCorpus straight
       away. If you want to regroup for some reason, you can, of course, still do that with the
       resulting GroupedCorpus.

       If you need a plain IterableCorpus as output, you can use ``no_group=True`` when calling
       this factory, which will produce the old behaviour.

    :param input_module_options: dictionary defining the module options for the input module, which
        will be provided to all the functions
    :param data_point_type: a data point type for the individual documents that will be produced. They
        do not need to be read in using this type's reading functionality, which will later be used for
        storing and reading the documents, but can be produced by some other means.
    :param data_ready_fn: function that takes the processed options given to the module in the
        config file and returns True if the data is ready to read, False otherwise. If execute_count
        is used, the data will be considered unready until the count has been run, even if this
        function returns True.
        Alternatively, may be a class to use as the reader for the dataset, instead of creating a new one
        dynamically. Then `len_fn` and `iter_fn` are not required (and will be ignored)
    :param iter_fn: function that takes a reader instance and returns a generator
        to iterate over the documents of the corpus. Like any IterableCorpus, it should yield pairs of
        (doc_name, doc). Reader options are available as `reader.setup.reader_options`.
    :param len_fn: function that takes the processed options given to the module in the
        config file and returns the number of docs
    :param module_type_name:
    :param module_readable_name:
    :param software_dependencies: a list of software dependencies that the module-info will return
        when ``get_software_dependencies()`` is called, or a function that takes the module-info instance and
        returns such a list. If left blank, no dependencies are returned.
    :param execute_count: make an executable module that counts the data to get its length (num docs)
    :param no_group: by default, the output datatype is a GroupedCorpus. If True, use an IterableCorpus
        instead without grouping documents into archives.
    :return: module info class
    """
    mt_name = module_type_name or "reader_for_{}".format(data_point_type.name)
    mr_name = module_readable_name or "Input reader for {} iterable corpus".format(data_point_type.name)
    corpus_type = IterableCorpus if no_group else GroupedCorpus
    output_datatype = corpus_type(data_point_type)

    if isinstance(data_ready_fn, types.FunctionType):
        # iter_fn and len_fn are required in this (the normal) case
        if iter_fn is None or len_fn is None:
            raise ValueError("iter_fn and len_fn are required unless specifying a whole reader class instead "
                             "of data_ready_fn")

        # Build a reader class using the given functions
        class FactoryInputReader(InputReader):
            def iterate(self):
                return iter_fn(self)

            class Setup(object):
                # NB execute_count is set below

                def check_data_ready(self):
                    return data_ready_fn(self.reader_options)

                def count(self):
                    return len_fn(self.reader_options)

        reader_cls = FactoryInputReader
    else:
        # A reader class has been given, so we don't need to create our own
        reader_cls = data_ready_fn
        data_ready_fn = None

    # Even if a reader class is given, make sure the execute_count flag is consistent with the main one
    reader_cls.Setup.execute_count = execute_count

    if not no_group:
        # Add some options to allow the config to control the grouper
        input_module_options = dict(input_module_options)
        input_module_options.update(GrouperModuleInfo.module_options)

    class IterableInputReaderModuleInfo(InputModuleInfo):
        module_type_name = mt_name
        module_readable_name = mr_name
        module_outputs = [("corpus", output_datatype)]
        module_options = input_module_options
        module_supports_python2 = python2

        # Special behaviour if we're making this an executable module in order to count the data
        module_executable = execute_count
        module_executor_override = DocumentCounterModuleExecutor if execute_count else None
        # Also make the reader class available so that it can be reused if necessary
        input_reader_class = reader_cls

        grouped = not no_group

        def get_software_dependencies(self):
            if software_dependencies is None:
                return []
            elif type(software_dependencies) is list:
                return software_dependencies
            else:
                return software_dependencies(self)

    return IterableInputReaderModuleInfo
