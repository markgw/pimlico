"""
The command-line iterable corpus browser displays one document at a time. It can display the raw data from the
corpus files, which sometimes is sufficiently human-readable to not need any special formatting. It can also
parse the data using its datatype and output text either from the datatype's standard unicode representation or,
if the document datatype provides it, a special browser formatting of the data.

When viewing output data, particularly during debugging of modules, it can be useful to provide special formatting
routines to the browser, rather than using or overriding the datatype's standard formatting methods. For example,
you might want to pull out specific attributes for each document to get an overview of what's coming out.

The browser command accepts a command-line option that specifies a Python class to format the data. This class
should be a subclass of :class:~pimlico.cli.browser.formatter.DocumentBrowserFormatter that accepts a datatype
compatible with the datatype being browsed and provides a method to format each document. You can write these
in your custom code and refer to them by their fully qualified class name.

"""
from pimlico.core.modules.base import check_type, TypeCheckError
from pimlico.datatypes.base import IterableCorpus, InvalidDocument
from pimlico.datatypes.documents import DataPointType


class DocumentBrowserFormatter(object):
    """
    Base class for formatters used to post-process documents for display in the iterable corpus browser.

    """
    """
    Should be overridden by subclasses to specify the corpus/document datatype(s) that can be formatted. Given in the
    same way as data-point types of iterable corpora, so expected to be a subclass of DataPointType.
    May also be an IterableCorpus subclass, in which case the corpus' data_point_type is used to check the formatted
    dataset's type.
    """
    DATATYPE = None

    """
    Whether the formatter expects to get the parsed document, according to the datatype's usual input reading
    routine, or just the raw text stored in the file. Usually it's the former (default), but subclasses may
    override this.
    """
    RAW_INPUT = False

    def __init__(self, corpus):
        self.corpus = corpus

    def format_document(self, doc):
        """
        Format a single document and return the result as a string (or unicode, but it will be converted to
        ASCII for display).

        Must be overridden by subclasses.

        """
        raise NotImplementedError

    def filter_document(self, doc):
        """
        Each doc is passed through this function directly after being read from the corpus. If None is returned,
        the doc is skipped. Otherwise, the result is used instead of the doc data. The default implementation
        does nothing.

        """
        return doc


class DefaultFormatter(DocumentBrowserFormatter):
    """
    Generic implementation of a browser formatter that's used if no other formatter is given.

    """
    DATATYPE = IterableCorpus

    def __init__(self, corpus, raw_data=False):
        super(DefaultFormatter, self).__init__(corpus)
        self.raw_data = raw_data

    def format_document(self, doc):
        if self.raw_data:
            # We're just showing the raw data, so don't try to do anything other than ensure it's a string
            doc = unicode(doc)
        else:
            # Allow datatypes to provide a custom way to format the data, other than the __unicode__
            try:
                doc = doc.browser_display
            except AttributeError:
                doc = unicode(doc)
        return doc


class InvalidDocumentFormatter(DocumentBrowserFormatter):
    """
    Formatter that skips over all docs other than invalid results. Uses standard formatting for InvalidDocument
    information.

    """
    DATATYPE = IterableCorpus

    def format_document(self, doc):
        return doc

    def filter_document(self, doc):
        return doc if isinstance(doc, InvalidDocument) else None


def load_formatter(dataset, formatter_name=None, parse=True):
    """
    Load a formatter specified by its fully qualified Python class name. If None, loads the default formatter.

    :param formatter_name: class name
    :param dataset: dataset that will be formatted
    :param parse: only used if the default formatter is loaded, determines `raw_data` (`= not parse`)
    :return: instantiated formatter
    """
    if formatter_name is not None:
        try:
            fmt_path, __, fmt_cls_name = formatter_name.rpartition(".")
            fmt_mod = __import__(fmt_path, fromlist=[fmt_cls_name])
        except ImportError, e:
            raise TypeError("Could not load formatter %s: %s" % (formatter_name, e))
        try:
            fmt_cls = getattr(fmt_mod, fmt_cls_name)
        except AttributeError, e:
            raise TypeError("Could not load formatter %s" % formatter_name)

        # If a formatter's given, use its attribute to determine whether we get raw input
        parse = not fmt_cls.RAW_INPUT

        # Check that the datatype provided is compatible with the formatter's datatype
        if issubclass(fmt_cls.DATATYPE, IterableCorpus):
            # Got a corpus type: use its document type to check compatibility
            document_type = fmt_cls.DATATYPE.data_point_type
        elif issubclass(fmt_cls.DATATYPE, DataPointType):
            # Was given a data-point type directly
            document_type = fmt_cls.DATATYPE
        else:
            raise TypeCheckError("formatter's datatype needs to be an iterable corpus subclass or a data-point type. "
                                 "Got %s" % fmt_cls.DATATYPE.__name__)

        if not issubclass(dataset.data_point_type, document_type):
            raise TypeCheckError(
                "formatter %s is not designed for this data-point type (%s)" %
                (formatter_name, dataset.data_point_type.__name__)
            )
        # Instantiate the formatter, providing it with the dataset
        formatter = fmt_cls(dataset)
    else:
        formatter = DefaultFormatter(dataset, raw_data=not parse)
    return formatter
