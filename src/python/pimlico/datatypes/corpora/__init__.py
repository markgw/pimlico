from collections import OrderedDict
from traceback import format_exc

from pimlico.cli.shell.base import ShellCommand
from pimlico.core.modules.options import opt_type_help
from pimlico.datatypes.base import PimlicoDatatype, DatatypeLoadError, DatatypeWriteError
from pimlico.datatypes.corpora.data_points import DataPointType
from pimlico.utils.core import import_member
from pimlico.utils.progress import get_progress_bar
from . import data_points
from . import tokenized


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


"""
This list collects together all the built-in data point types. These can be specified 
using only their class name, rather than requiring a fully-qualified path, when giving 
a data point type in a config file
"""
DATA_POINT_TYPES = [
    data_points.RawDocumentType,
    data_points.RawTextDocumentType, data_points.TextDocumentType,
    tokenized.TokenizedDocumentType, tokenized.CharacterTokenizedDocumentType, tokenized.SegmentedLinesDocumentType,
]


@opt_type_help("Data point type, class name of a core type or fully qualified path")
def data_point_type_opt(text):
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
    from this type directly: use a subtype, like :cls:`~pimlico.datatypes.grouped.GroupedCorpus`, instead.

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
            "required": True,
            "help": "Required data point type for the iterable corpus. This is used to process each "
                    "document in the corpus in an appropriate way. Should be a subclass of DataPointType"
        })
    ] + PimlicoDatatype.datatype_options.items())

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

    class Reader:
        def __len__(self):
            try:
                return self.metadata["length"]
            except KeyError:
                raise DatatypeLoadError("no length found in metadata for %s corpus. It is an iterable corpus, so if it "
                                        "is ready to use, the length should have been stored. Metadata keys found: %s" %
                                        (self.datatype.datatype_name, self.metadata.keys()))

        def get_detailed_status(self):
            return super(self.__class__, self).get_detailed_status() + ["Length: %d" % len(self)]

        def __iter__(self):
            """
            Subclasses should implement an iter method that simply iterates over all the documents in the
            corpus in a consistent order. They may also provide other methods for iterating over or otherwise
            accessing the data.

            TODO: The following documentation will need to be updated once the document typing system is redesigned

            Each yielded document should consist of a pair `(name, doc)`, where `name` is an identifier for the document
            (e.g. filename) and `doc` is the document's data, in the appropriate type.

            You may wish to call `process_document_data_with_datatype()` on the raw content to apply the data-point
            type's standard processing to it.

            """
            raise NotImplementedError

        def data_to_document(self, data):
            """
            Applies the corpus' datatype's processing to the raw data, given as a
            unicode string, and produces a document instance.

            :param data: unicode string of raw data
            :return: document instance
            """
            # Catch invalid documents
            document = InvalidDocument.invalid_document_or_text(data)
            # Apply subclass-specific post-processing if we've not been asked to yield just the raw data
            if type(document) is not InvalidDocument:
                try:
                    # Produce a document instance of the appropriate type
                    document = self.datatype.data_point_type(document)
                except BaseException, e:
                    # If there's any problem reading in the document, yield an invalid doc with the error
                    document = InvalidDocument(
                        "datatype %s reader" % self.datatype.data_point_type.name,
                        "{}: {}".format(e, format_exc())
                    )
            return document

    def check_type(self, supplied_type):
        """
        Override type checking to require that the supplied type have a document type that is compatible with
        (i.e. a subclass of) the document type of this class.

        """
        main_type_check = super(IterableCorpus, self).check_type(supplied_type)
        return main_type_check and issubclass(supplied_type.data_point_type, self.data_point_type)

    def type_checking_name(self):
        return "%s<%s>" % (super(IterableCorpus, self).type_checking_name(), self.data_point_type.name)

    def full_datatype_name(self):
        return "%s<%s>" % (self.datatype_name, self.data_point_type.name)


class IterableCorpusWriter(object):
    """
    TODO Provide when writer system is implemented (as IterableCorpus.Writer)

    NB: IterableCorpus itself has no particular way of storing files, so this is only here to
    ensure that all subclasses (e.g. GroupedCorpus) store a length in the same way.

    """
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
