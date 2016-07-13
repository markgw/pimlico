"""
Document types used to represent datatypes of individual documents in an IterableCorpus or subtype.

"""


class DataPointType(object):
    """
    Base data-point type for iterable corpora. All iterable corpora should have data-point types that are
    subclasses of this.

    """
    input_module_options = {}

    def __init__(self, options, metadata):
        self.metadata = metadata
        self.options = options


class RawDocumentType(DataPointType):
    """
    Base document type. All document types for tarred corpora should be subclasses of this.

    It may be used itself as well, where documents are just treated as raw data, though most of the time it will
    be appropriate to use subclasses to provide more information and processing operations specific to the
    datatype.

    """
    def process_document(self, doc):
        return doc


class RawTextDocumentType(RawDocumentType):
    """
    Subclass of RawDocumentType used to indicate that the document represents text (not just any old raw data)
    and that it hasn't been processed (tokenized, etc). Note that text that has been tokenized, parsed, etc does
    not used subclasses of this type, so they will not be considered compatible if this type is used as a
    requirement.

    """