# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Document types used to represent datatypes of individual documents in an IterableCorpus or subtype.

"""

__all__ = ["DataPointType", "RawDocumentType", "RawTextDocumentType"]


class DataPointType(object):
    """
    Base data-point type for iterable corpora. All iterable corpora should have data-point types that are
    subclasses of this.

    """
    input_module_options = {}
    #: List of (name, cls_path) pairs specifying a standard set of formatters that the user might want to choose from to
    #: view a dataset of this type. The user is not restricted to this set, but can easily choose these by name,
    #: instead of specifying a class path themselves.
    #: The first in the list is the default used if no formatter is specified. Falls back to DefaultFormatter if empty
    formatters = []

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
    input_module_options = {
        "encoding": {
            "help": "Encoding to assume for input files. Default: utf8",
            "default": "utf8",
        },
    }

    def process_document(self, doc):
        if type(doc) is unicode:
            # Decoding's already been done
            return doc
        else:
            return doc.decode(self.options.get("encoding", "utf8"))
