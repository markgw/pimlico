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
from traceback import format_exc

from pimlico.datatypes.base import IterableCorpus


class DocumentBrowserFormatter(object):
    """
    Base class for formatters used to post-process documents for display in the iterable corpus browser.

    """
    """
    Should be overridden by subclasses to specify the corpus datatype(s) that can be formatted. Given in the
    same way as input datatypes to modules, so may be a subclass of IterableCorpus, a DynamicInputDatatypeRequirement,
    or a tuple of requirements.
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
