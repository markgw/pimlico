# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from __future__ import print_function
from builtins import object

from collections import OrderedDict
from traceback import format_exc

import sys

from pimlico.cli.shell.base import ShellCommand
from pimlico.core.modules.options import opt_type_help
from pimlico.datatypes.base import PimlicoDatatype, DatatypeLoadError, DatatypeWriteError
from pimlico.datatypes.corpora.data_points import DataPointType, is_invalid_doc, \
    invalid_document_or_raw, invalid_document
from pimlico.utils.core import import_member
from pimlico.utils.progress import get_progress_bar


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
            (1 if is_invalid_doc(doc) else 0) for __, doc in pbar(corpus)
        )
        print("%d / %d documents are invalid" % (invalids, len(corpus)))


@opt_type_help("Data point type, class name of a core type or fully qualified path")
def data_point_type_opt(text):
    from . import DATA_POINT_TYPES
    text = text.strip("\n ")
    # Check whether this refers to one of the core types
    for cls in DATA_POINT_TYPES:
        if cls.__name__ == text:
            break
    else:
        # Try to load the class from a fully qualified path
        cls = import_member(text)
    # Instantiate the datatype
    return cls()


class IterableCorpus(PimlicoDatatype):
    """
    Superclass of all datatypes which represent a dataset that can be iterated over document by document
    (or datapoint by datapoint - what exactly we're iterating over may vary, though documents are most common).

    This is an abstract base class and doesn't provide any mechanisms for storing documents or organising
    them on disk in any way. Many input modules will override this to provide a reader that iterates
    over the documents directly, according to IterableCorpus' interface. The main subclass of this used
    within pipelines is GroupedCorpus, which provides an interface for iterating over groups of
    documents and a storage mechanism for grouping together documents in archives on disk.

    May be used as a type requirement, but remember that it is not possible to create a reader
    from this type directly: use a subtype, like :class:`~pimlico.datatypes.grouped.GroupedCorpus`, instead.

    The actual type of the data depends on the type given as the first argument,
    which should be an instance of DataPointType or a subclass: it could be, e.g. coref output, etc.
    Information about
    the type of individual documents is provided by `data_point_type` and this is used in type checking.

    Note that the data point type is the first datatype option, so can be given as the
    first positional arg when instantiating an iterable corpus subtype:

    .. code:: py

       corpus_type = GroupedCorpus(RawTextDocumentType())
       corpus_reader = corpus_type("... base dir path ...")

    At creation time, length should be provided in the metadata, denoting how many documents are in the dataset.

    """
    datatype_name = "iterable_corpus"
    shell_commands = PimlicoDatatype.shell_commands + [CountInvalidCmd()]
    datatype_options = OrderedDict([
        ("data_point_type", {
            "type": data_point_type_opt,
            "default": DataPointType(),
            "help": "Data point type for the iterable corpus. This is used to process each "
                    "document in the corpus in an appropriate way. Should be a subclass of DataPointType. "
                    "This should almost always be given, typically as the first positional arg when instantiating "
                    "the datatype. Defaults to the generic data point type at the top of the hierarchy"
        })
    ] + list(PimlicoDatatype.datatype_options.items()))

    def __init__(self, *args, **kwargs):
        super(IterableCorpus, self).__init__(*args, **kwargs)
        # Data point type has been given as an option (possibly via a positional arg)
        # Make it easily available
        self.data_point_type = self.options["data_point_type"]

        if not isinstance(self.data_point_type, DataPointType):
            # Easy mistake: pass in a data point type class instead of an instance
            if type(self.data_point_type) is type and issubclass(self.data_point_type, DataPointType):
                raise TypeError("data point type should be an instance of a data point type, not a class: got {cls}, "
                                "which probably should have been {cls}()".format(cls=self.data_point_type.__name__))
            raise TypeError("data point type for iterable corpus must be an instance of "
                            "DataPointType or of one of its subclasses")

    def __call__(self, *args, **kwargs):
        # Check we're not creating a reader directly from IterableCorpus, which is abstract
        if type(self) is IterableCorpus:
            raise TypeError("tried to create a reader from iterable corpus type: use a subtype, like "
                            "GroupedCorpus, instead")
        return super(IterableCorpus, self).__call__(*args, **kwargs)

    def run_browser(self, reader, opts):
        from pimlico.cli.browser.tools.formatter import load_formatter
        from pimlico.cli.browser.tools.corpus import browse_data

        # Catch the special formatter value 'help' that lists available standard formatters
        if opts.formatter == "help":
            standard_formatters = self.data_point_type.formatters
            if len(standard_formatters) == 0:
                print("\nDatatype does not define any standard formatters.")
                print("If you don't specify one, the default formatter will be used (raw data)")
            else:
                print("\nStandard formatters for datatype: %s" % ", ".join(name for (name, cls) in standard_formatters))
                print("These can be selected by name using the --formatter option.")
                print("If no formatter is selected, %s will be used" % standard_formatters[0][0])
            sys.exit(0)

        # Check we've got urwid installed
        try:
            import urwid
        except ImportError:
            print("You need Urwid to run the browser: install by running 'make urwid' in the Python lib dir")
            sys.exit(1)

        # Load the formatter if one was requested
        try:
            formatter = load_formatter(self, opts.formatter)
        except TypeError as e:
            print("Error loading formatter", file=sys.stderr)
            print(e, file=sys.stderr)
            sys.exit(1)

        browse_data(reader, formatter, skip_invalid=opts.skip_invalid)

    class Reader(object):
        def __init__(self, *args, **kwargs):
            super(IterableCorpus.Reader, self).__init__(*args, **kwargs)
            # Call the data point type's reader_init() method to allow it to do anything
            # that should be done when the reader is prepared
            self.datatype.data_point_type.reader_init(self)

        def __len__(self):
            try:
                return self.metadata["length"]
            except KeyError:
                raise DatatypeLoadError("no length found in metadata for %s corpus. It is an iterable corpus, so if it "
                                        "is ready to use, the length should have been stored. Metadata keys found: %s" %
                                        (self.datatype.datatype_name, list(self.metadata.keys())))

        def get_detailed_status(self):
            return super(IterableCorpus.Reader, self).get_detailed_status() + ["Length: {:,}".format(len(self))]

        def __iter__(self):
            """
            Subclasses should implement an iter method that simply iterates over all the documents in the
            corpus in a consistent order. They may also provide other methods for iterating over or otherwise
            accessing the data.

            Each yielded document should consist of a pair `(name, doc)`,
            where `name` is an identifier for the document (e.g. filename)
            and `doc` is an instance of the appropriate document type.

            """
            raise NotImplementedError

        def data_to_document(self, data, metadata=None):
            """
            Applies the corpus' datatype's processing to the raw data, given as a
            bytes object, and produces a document instance.

            :param metadata: dict containing doc metadata (optional)
            :param data: bytes raw data
            :return: document instance
            """
            # Catch invalid documents
            data = invalid_document_or_raw(data)
            if is_invalid_doc(data):
                return data
            # Apply subclass-specific post-processing if we've not been asked to yield just the raw data
            try:
                # Produce a document instance of the appropriate type
                document = self.datatype.data_point_type(raw_data=data, metadata=metadata)
            except BaseException as e:
                # If there's any problem reading in the document, yield an invalid doc with the error
                document = invalid_document(
                    u"datatype %s reader" % self.datatype.data_point_type.name,
                    u"{}: {}".format(e, format_exc())
                )
            return document

    class Writer(object):
        """
        Stores the length of the corpus.

        NB: IterableCorpus itself has no particular way of storing files, so this is only here to
        ensure that all subclasses (e.g. GroupedCorpus) store a length in the same way.

        """
        metadata_defaults = {
            "length": (
                None,
                "Number of documents in the corpus. Must be set by the writer, otherwise "
                "an exception will be raised at the end of writing"
            ),
        }

        def __init__(self, datatype, *args, **kwargs):
            # Add the data point type's metadata defaults to our dictionary
            self.metadata_defaults = dict(self.metadata_defaults, **datatype.data_point_type.metadata_defaults)
            super(IterableCorpus.Writer, self).__init__(datatype, *args, **kwargs)
            # Call the data point type's writer_init() method to allow it to do anything
            # that should be done when the writer is prepared
            datatype.data_point_type.writer_init(self)

        def __exit__(self, exc_type, exc_val, exc_tb):
            super(IterableCorpus.Writer, self).__exit__(exc_type, exc_val, exc_tb)
            # Check the length has been set
            if self.metadata["length"] is None:
                raise DatatypeWriteError("writer for IterableDocumentCorpus must set a 'length' value in the metadata")

    def check_type(self, supplied_type):
        """
        Override type checking to require that the supplied type have a document type that is compatible with
        (i.e. a subclass of) the document type of this class.

        The data point types can also introduce their own checks, other than simple isinstance checks.

        """
        main_type_check = super(IterableCorpus, self).check_type(supplied_type)
        return main_type_check and self.data_point_type.check_type(supplied_type.data_point_type)

    def type_checking_name(self):
        return "%s<%s>" % (super(IterableCorpus, self).type_checking_name(), self.data_point_type.name)

    def full_datatype_name(self):
        return "%s<%s>" % (self.datatype_name, self.data_point_type.name)
