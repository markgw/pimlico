# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Base classes and utilities for input modules in a pipeline.

"""

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.core.modules.execute import ModuleExecutionError
from pimlico.datatypes import PimlicoDatatype
from pimlico.datatypes.base import PimlicoDatatypeReaderMeta
from pimlico.datatypes.corpora import IterableCorpus
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

        def instantiate_output_reader_setup(self, output_name, datatype):
            # Create a reader setup that just has the given directory as a possible location for the data
            return datatype([self.options["dir"]])

    return DatatypeInputModuleInfo


def iterable_input_reader(input_module_options, data_point_type,
                          data_ready_fn, len_fn, iter_fn,
                          module_type_name=None, module_readable_name=None,
                          software_dependencies=None, execute_count=False):
    """
    Factory for creating an input reader module info. This is a non-executable module that has no
    inputs. It reads its data from some external location, using the given module options. The resulting
    dataset is an IterableCorpus, with the given document type.

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

    :param iter_fn: function that takes a reader instance and returns a generator
        to iterate over the documents of the corpus. Like any IterableCorpus, it should yield pairs of
        (doc_name, doc). Reader options are available as `reader.setup.reader_options`.
    :param len_fn: function that takes the reader (which makes options available) and returns the number of docs
    :param input_module_options:
    :param data_point_type: a data point type for the individual documents that will be produced. They
        do not need to be read in using this type's reading functionality, which will later be used for
        storing and reading the documents, but can be produced by some other means.
    :param data_ready_fn: function that takes the processed options given to the module in the
        config file and returns True if the data is ready to read, False otherwise. If execute_count
        is used, the data will be considered unready until the count has been run, even if this
        function returns True.
    :param module_type_name:
    :param module_readable_name:
    :param software_dependencies: a list of software dependencies that the module-info will return
        when ``get_software_dependencies()`` is called, or a function that takes the module-info instance and
        returns such a list. If left blank, no dependencies are returned.
    :param execute_count: make an executable module that counts the data to get its length (num docs)
    :return: module info class
    """
    mt_name = module_type_name or "reader_for_{}".format(data_point_type.name)
    mr_name = module_readable_name or "Input reader for {} iterable corpus".format(data_point_type.name)

    class InputReader(PimlicoDatatype.Reader):
        __metaclass__ = PimlicoDatatypeReaderMeta

        def __init__(self, *args, **kwargs):
            super(InputReader, self).__init__(*args, **kwargs)
            # Provide easy access to the options from the config
            self.options = self.setup.reader_options

        class Setup:
            def __init__(self, datatype, output_dir, reader_options):
                self.datatype = datatype
                self.reader_options = reader_options
                self.output_dir = output_dir

            def ready_to_read(self):
                # If executing a count, make sure the result is ready before we read the data
                if execute_count and self.read_metadata(self.output_dir).get("length", None) is None:
                    return False
                return data_ready_fn(self.reader_options)

        def __len__(self):
            if "length" in self.metadata:
                # If the length has been stored, use that
                return self.metadata["length"]
            else:
                return len_fn(self)

        def __iter__(self):
            return iter_fn(self)

        def process_setup(self):
            """ Override so we don't try to get base_dir, etc, as the standard reader does """
            return

        def _get_metadata(self):
            if execute_count:
                return self.setup.read_metadata(self.setup.output_dir)
            else:
                return {}
        metadata = property(_get_metadata)

    if execute_count:
        class DocumentCounterModuleExecutor(BaseModuleExecutor):
            """
            An executor that just calls the len method to count documents and stores the result

            """
            def execute(self):
                datatype = self.info.get_output_datatype("corpus")
                reader_options = datatype.reader_options

                self.log.info("Counting documents in corpus")
                num_docs = len_fn(reader_options)
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

                self.log.info("Corpus contains {} docs. Storing count".format(num_docs))
                with self.info.get_output_writer("corpus") as writer:
                    writer.metadata["length"] = num_docs
                    if num_valid_docs is not None:
                        writer.metadata["valid_documents"] = num_valid_docs


    class IterableInputReaderModuleInfo(InputModuleInfo):
        module_type_name = mt_name
        module_readable_name = mr_name
        module_outputs = [("corpus", IterableCorpus(data_point_type))]
        module_options = input_module_options

        # Special behaviour if we're making this an executable module in order to count the data
        module_executable = execute_count
        module_executor_override = DocumentCounterModuleExecutor if execute_count else None
        # Also make the reader class available so that it can be reused if necessary
        input_reader_class = InputReader

        def instantiate_output_reader_setup(self, output_name, datatype):
            return InputReader.Setup(datatype, self.get_absolute_output_dir(output_name), self.options)

        def get_software_dependencies(self):
            if software_dependencies is None:
                return []
            elif type(software_dependencies) is list:
                return software_dependencies
            else:
                return software_dependencies(self)

    return IterableInputReaderModuleInfo
