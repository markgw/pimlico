# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Base classes and utilities for input modules in a pipeline.

"""

from pimlico.core.modules.base import BaseModuleExecutor
from pimlico.core.modules.execute import ModuleExecutionError
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


def iterable_input_reader(input_module_options, data_point_type,
                          data_ready_fn, len_fn, iter_fn,
                          module_type_name=None, module_readable_name=None,
                          software_dependencies=None, execute_count=False):
    """
    This is a new version of the factory :func:`.iterable_input_reader_factor` and should be
    used where possible. It provides a nicer interface using the new datatypes system.

    Factory for creating an input reader module type. This is a non-executable module that has no
    inputs. It reads its data from some external location, using the given module options. The resulting
    dataset is an IterableCorpus, with the given document type.

    If execute_count=True, the module will be an executable module and the execution will simply count
    the number of documents in the corpus and store the count. This should be used if counting the documents
    in the dataset is not completely trivial and quick (e.g. if you need to read through the data itself,
    rather than something like counting files in a directory or checking metedata).
    It is common for this to be the only processing that needs to be done on the dataset before using it.
    The len_fn is used to count the documents in the module's execution phase.

    If the counting method returns a pair of integers, instead of just a single integer,
    they are taken to be the total number of documents in the corpus and the number of valid documents
    (i.e. the number that will be produce an InvalidDocument). In this case, the valid documents count
    is also stored in the metadata, as ``valid_documents``.

    Reader options are available at read time from the datatype instance's ``reader_options`` attribute.
    You can get this from the reader instance by ``reader.options``.

    .. todo::

       Change the way this is done slightly. Under the new datatype system, you
       shouldn't create a special output datatype, but use the actual datatype that
       will be produced. Instead create a special *reader*, which gets instantiated
       by the module (using ``instantiate_output_reader()``).

    :param iter_fn: function that takes a reader instance and returns a generator
        to iterate over the documents of the corpus. Like any IterableCorpus, it should yield pairs of
        (doc_name, doc)
    :param len_fn: function that takes the reader options and returns the number of docs
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
    :return:
    """
    mt_name = module_type_name or "reader_for_{}".format(data_point_type.name)
    mr_name = module_readable_name or "Input reader for {} iterable corpus".format(data_point_type.name)

    class ReaderOutputType(IterableCorpus):
        """
        A datatype for reading in input according to input module options and allowing it to
        be iterated over by other modules.

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
            # If executing a count, make sure the result is ready before we read the data
            if execute_count and self._read_metadata(base_dir).get("length", None) is None:
                return False
            return data_ready_fn(base_dir, self.reader_options)

        class Reader:
            def __init__(self, *args, **kwargs):
                super(self.__class__, self).__init__(*args, **kwargs)
                self.options = self.datatype.reader_options

            def __len__(self):
                if "length" in self.metadata:
                    # If the length has been stored, use that
                    return self.metadata["length"]
                else:
                    return len_fn(self.options)

            def __iter__(self):
                return iter_fn(self)

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
        module_outputs = [("corpus", ReaderOutputType(data_point_type))]
        module_options = input_module_options

        # Special behaviour if we're making this an executable module in order to count the data
        module_executable = execute_count
        module_executor_override = DocumentCounterModuleExecutor if execute_count else None

        def get_output_datatype(self, output_name=None):
            # TODO Use instantiate_output_reader() here instead of this
            name, dt = super(IterableInputReaderModuleInfo, self).get_output_datatype(output_name=output_name)
            dt.set_reader_options(self.options)
            return name, dt

        def get_software_dependencies(self):
            if software_dependencies is None:
                return []
            elif type(software_dependencies) is list:
                return software_dependencies
            else:
                return software_dependencies(self)

    return IterableInputReaderModuleInfo
