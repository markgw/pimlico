# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Base classes and utilities for input modules in a pipeline.

"""

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.datatypes.corpora import IterableCorpus
from pimlico.old_datatypes.base import IterableCorpusWriter
from .base import BaseModuleInfo


class InputModuleInfo(BaseModuleInfo):
    """
    Base class for input modules. These don't get executed in general, they just provide a way to iterate over
    input data.

    You probably don't want to subclass this. It's usually simplest to define a datatype for reading the input
    data and then just specify its class as the module's type. This results in a subclass of this module info
    being created dynamically to read that data.

    Note that module_executable is typically set to False and the base class does this. However, some input
    modules need to be executed before the input is usable, for example to collect stats about the input
    data.

    """
    module_type_name = "input"
    module_executable = False

    def instantiate_output_datatype(self, output_name, output_datatype, **kwargs):
        return output_datatype(self.options["dir"], self.pipeline, module=self)


def input_module_factory(datatype):
    """
    Create an input module class to load a given datatype.

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

    return DatatypeInputModuleInfo


class ReaderOutputType(IterableCorpus):
    """
    A datatype for reading in input according to input module options and allowing it to
    be iterated over by other modules.

    Typically used together with `iterable_input_reader_factory()` as the output datatype.

    ``__len__`` should be overridden to take the processed input module options and return
    the length of the corpus (number of documents).

    ``__iter__`` should use the processed input module options and return an iterator over the
    corpus' documents (e.g. a generator function). Each item yielded should be a pair ``(doc_name, data)``
    and ``data`` should be in the appropriate internal format associated with the document type.

    ``data_ready`` should be overridden to use the processed input module options and return True if the data
    is ready to be read in.

    In all cases, the input options are available as ``self.reader_options``.

    On the Document, override __len__ to compute length using self.reader_options,
    unless you use execute_count.
    Also override __iter__ to iterate over documents using self.reader_options.

    """
    datatype_name = "reader_iterator"
    #: Subclass information should be ignored for type checking. Should be treated exactly as an IterableCorpus
    emulated_datatype = IterableCorpus

    def __init__(self, *args, **kwargs):
        super(ReaderOutputType, self).__init__(*args, **kwargs)
        self.reader_options = None

    def set_reader_options(self, options):
        """
        Use the given set of options for reading the input. These are not datatype
        options, as they do not relate to the nature of the produced output type.
        They are options that affect the way to data is read in from disk, so are
        provided to the special input reader output type's Reader in this way.

        """
        self.reader_options = options

    def data_ready(self, base_dir):
        raise NotImplementedError("ReaderOutputType should override data_ready() to check whether the data is "
                                  "ready to read")


class DocumentCounterModuleExecutor(BaseModuleExecutor):
    """
    An executor that just calls the __len__ method to count documents and stores the result

    """
    def execute(self):
        # Instantiate the output corpus so we can count the docs
        output_corpus = self.info.get_output("corpus")

        if not hasattr(output_corpus, "count_documents"):
            raise ModuleExecutionError("input reader '{}' was defined as having a document count execution "
                                       "phase, but does not implement a count_documents() method".format(
                output_corpus.datatype_name
            ))

        self.log.info("Counting documents in corpus")
        num_docs = output_corpus.count_documents()
        num_valid_docs = None

        if type(num_docs) is tuple:
            # A pair of values was returned: this is the num docs and num valid docs
            if len(num_docs) > 2:
                raise ModuleExecutionError("input reader '{}' return a tuple document count with {} values. "
                                           "Expected either one or two values (num docs and num valid docs)".format(
                    output_corpus.datatype_name, len(num_docs)
                ))
            elif len(num_docs) == 1:
                num_docs = num_docs[0]
            else:
                num_docs, num_valid_docs = num_docs

        self.log.info("Corpus contains {} docs. Storing count".format(num_docs))
        with IterableCorpusWriter(self.info.get_absolute_output_dir("corpus")) as writer:
            writer.metadata["length"] = num_docs
            if num_valid_docs is not None:
                writer.metadata["valid_documents"] = num_valid_docs


def decorate_require_stored_len(obj):
    """
    Decorator for a data_ready() function that requires the data's length to have been computed.
    Used when execute_count==True.
    """
    old_data_ready = obj.data_ready
    def new_data_ready():
        if "length" not in obj.metadata:
            return False
        else:
            return old_data_ready
    obj.data_ready = new_data_ready


def iterable_input_reader_factory(input_module_options, output_type, module_type_name=None, module_readable_name=None,
                                  software_dependencies=None, execute_count=False):
    """
    Factory for creating an input reader module type. This is a non-executable module that has no
    inputs. It reads its data from some external location, using the given module options. The resulting
    dataset is an IterableCorpus subtype, with the given document type.

    ``output_type`` is a datatype that performs the actual iteration over the data and is instantiated
    with the processed options as its first argument. This is typically created by subclassing ReaderOutputType
    and providing len, iter and data_ready methods.

    ``software_dependencies`` may be a list of software dependencies that the module-info will return
    when ``get_software_dependencies()`` is called, or a function that takes the module-info instance and
    returns such a list. If left blank, no dependencies are returned.

    If ``execute_count==True``, the module will be an executable module and the execution will simply count
    the number of documents in the corpus and store the count. This should be used if counting the documents
    in the dataset is not completely trivial and quick (e.g. if you need to read through the data itself,
    rather than something like counting files in a directory or checking metedata).
    It is common for this to be the only processing that needs to be done on the dataset before using it.
    The ``output_type`` should then implement a ``count_documents()`` method.
    The ``__len__`` method then simply use the computed and stored value. There is no need to override it.

    If the ``count_documents()`` method returns a pair of integers, instead of just a single integer,
    they are taken to be the total number of documents in the corpus and the number of valid documents
    (i.e. the number that will be produce an InvalidDocument). In this case, the valid documents count
    is also stored in the metadata, as ``valid_documents``.

    **How is this different from ``input_module_factory``?** This method is used in your module code
    to prepare a ModuleInfo class for reading a particular type of input data and presenting it as a
    Pimlico dataset of the given type. ``input_module_factory``, on the other hand, is used by Pimlico
    when you specify a datatype as a module type in a config file.

    Note that, in future versions, reading datasets output by another Pimlico pipeline will be the only
    purpose for that special notation. The possibility of specifying ``input_module_options`` to create
    an input reader will disappear, so the use of ``input_module_options`` should be phased out and replaced
    with input reader modules, such as those created by this factory.

    """
    mt_name = module_type_name or "reader_for_{}".format(output_type.data_point_type.name)
    mr_name = module_readable_name or "Input reader for {} iterable corpus".format(output_type.data_point_type.name)

    class IterableInputReaderModuleInfo(InputModuleInfo):
        module_type_name = mt_name
        module_readable_name = mr_name
        module_outputs = [("corpus", output_type)]
        module_options = input_module_options

        # Special behaviour if we're making this an executable module in order to count the data
        module_executable = execute_count
        module_executor_override = DocumentCounterModuleExecutor if execute_count else None

        def instantiate_output_datatype(self, output_name, output_datatype, **kwargs):
            base_dir = None
            if execute_count:
                # If executing to provide a length, we need the corpus to have a base dir so it finds the count
                base_dir = self.get_output_dir("corpus")

            # Set the reader options on the datatype, which control how the reader will read in the data
            output_type.set_reader_options(self.options)
            corpus = output_type(base_dir, self.pipeline)

            if execute_count:
                # Wrap the data_ready() in a decorator that checks the length has been counted
                decorate_require_stored_len(corpus)
            return corpus

        def get_software_dependencies(self):
            if software_dependencies is None:
                return []
            elif type(software_dependencies) is list:
                return software_dependencies
            else:
                return software_dependencies(self)

    return IterableInputReaderModuleInfo
