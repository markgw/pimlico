# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Document types used to represent datatypes of individual documents in an IterableCorpus or subtype.

"""

__all__ = ["DataPointType", "RawDocumentType", "TextDocumentType", "RawTextDocumentType", "DataPointError",
           "InvalidDocument"]


class DataPointType(object):
    """
    Base data-point type for iterable corpora. All iterable corpora should have data-point types that are
    subclasses of this.

    .. note::

       For now, data point types don't have a way of specifying options (like main datatypes do).
       I'm not sure whether this is needed, so I'm leaving it out for now. If it is needed, an
       additional datatype option can be added to iterable corpora that allows you to specify
       data point type options for when a datatype is being loaded using a config file.

    """
    #: List of (name, cls_path) pairs specifying a standard set of formatters that the user might want to choose from to
    #: view a dataset of this type. The user is not restricted to this set, but can easily choose these by name,
    #: instead of specifying a class path themselves.
    #: The first in the list is the default used if no formatter is specified. Falls back to DefaultFormatter if empty
    formatters = []

    def __call__(self, data, from_internal=False):
        """
        Produce a document of this type, using the raw data unicode string to instantiate
        the document's data from.

        If `from_internal=True`, the given data is the document's internal data
        dictionary, not a unicode string. You may do this, for example, if you're
        modifying a document's data and producing a document of a subtype.

        """
        if from_internal:
            raw_data = None
            internal_data = data
        else:
            raw_data = data
            internal_data = None
        doc_cls = self._get_document_cls()
        return doc_cls(self, raw_data=raw_data, internal_data=internal_data)

    def __repr__(self):
        return "{}()".format(self.name)

    @property
    def name(self):
        return self.__class__.__name__

    def is_type_for_doc(self, doc):
        """
        Check whether the given document is of this type, or a subclass of this one.

        """
        return isinstance(doc.data_point_type, type(self))

    @classmethod
    def _get_document_cls(cls):
        # Cache document subtyping, so that the same type object is returned from repeated calls on the
        # same document type
        if not hasattr(cls, "__document_type"):
            if cls is DataPointType:
                # On the base class, we just return the base document
                cls.__document_type = cls.Document
            else:
                parent_doc_cls = cls.__bases__[0]._get_document_cls()

                my_doc_cls = cls.Document
                if parent_doc_cls is my_doc_cls:
                    # Document is not overridden, so we don't need to subclass
                    cls.__document_type = parent_doc_cls
                else:
                    # Perform subclassing so that a new Document is created that is a subclass of the parent's document
                    type_name = cls.__name__
                    if type_name.endswith("Type"):
                        # To get the class name, we typically remove "Type" from the end of the data point type class name
                        doc_name = type_name[:-4]
                    else:
                        # If the class name didn't follow the pattern of ending with "Type",
                        # add "Document" instead to distinguish it
                        doc_name = "{}Document".format(type_name)

                    cls.__document_type = type(doc_name, (parent_doc_cls,), my_doc_cls.__dict__)
        return cls.__document_type

    class Document(object):
        """
        The abstract superclass of all documents.

        You do not need to subclass or instantiate these yourself: subclasses are created automatically
        to correspond to each document type. You can add functionality to a datapoint type's document
        by creating a nested `Document` class. This will inherit from the parent datapoint type's document.
        This happens automatically - you don't need to do it yourself and shouldn't inherit from anything:

        .. code-block:: py
           class MyDataPointType(DataPointType):
               class Document:
                   # Overide document things here
                   # Add your own methods, properties, etc for getting data from the document

        Each document type should provide a method to convert from raw data (a unicode string) to the
        internal representation (an arbitrary dictionary) called `raw_to_internal()`, and another to convert
        the other way called `internal_to_raw()`. Both forms of the data are available using the
        properties `raw_data` and `internal_data`, and these methods are called as necessary to
        convert back and forth.

        This is to avoid unnecessary conversions. For example, if the raw data is supplied
        and then only the raw data is ever used (e.g. passing the document straight through
        and writing out to disk), we want to avoid converting back and forth.

        A subtype should then supply methods or properties (typically using the cached_property
        decorator) to provide access to different parts of the data. See the many built-in
        document types for examples of doing this.

        You should not generally need to override the `__init__` method. You may, however, wish to
        override `internal_available()` or `raw_available()`. These are called as soon as the
        internal data or raw data, respectively, become available, which may be at instantiation
        or after conversion. This can be useful if there are bits of computation that you want
        to do on the basis of one of these and then store to avoid repeated computation.

        """
        def __init__(self, data_point_type, raw_data=None, internal_data=None):
            self.data_point_type = data_point_type

            if raw_data is None and internal_data is None:
                raise DataPointError("either raw_data or internal_data must be given when instantiating a document")
            if raw_data is not None and internal_data is not None:
                raise DataPointError("only one of raw_data and internal_data may be given when "
                                     "instantiating a document")

            self._raw_data = raw_data
            self._internal_data = internal_data

            if self._raw_data is not None:
                self.raw_available()
            if self._internal_data is not None:
                self.internal_available()

        def raw_to_internal(self, raw_data):
            """
            Take a unicode string containing the raw data for a document, read in from disk,
            and produce a dictionary containing all the processed data in the document's
            internal format.

            You will often want to call the super method and replace values or add to the
            dictionary. Whatever you do, make sure that all the internal data that the
            super type provides is also provided here, so that all of its properties and
            methods work.

            """
            raise NotImplementedError(
                "document type '{}' does not implement raw_to_internal()".format(self.data_point_type))

        def internal_to_raw(self, internal_data):
            """
            Take a dictionary containing all the document's data in its internal format
            and produce a unicode string containing all that data, which can be written
            out to disk.

            """
            raise NotImplementedError(
                "document type '{}' does not implement internal_to_raw()".format(self.data_point_type))

        def raw_available(self):
            """
            Called as soon as the raw data becomes available, either at instantiation or
            conversion.

            """
            return

        def internal_available(self):
            """
            Called as soon as the internal data becomes available, either at instantiation or
            conversion.

            """
            return

        def __repr__(self):
            return "{}()".format(self.__class__.__name__)

        @property
        def raw_data(self):
            if self._raw_data is None:
                # Raw data not available yet: convert from internal data
                self._raw_data = self.internal_to_raw(self._internal_data)
                self.raw_available()
            return self._raw_data

        @property
        def internal_data(self):
            if self._internal_data is None:
                # Internal data not available yet: convert from raw
                self._internal_data = self.raw_to_internal(self._raw_data)
                self.internal_available()
            return self._internal_data


class InvalidDocument(DataPointType):
    """
    Widely used in Pimlico to represent an empty document that is empty not because the original input document
    was empty, but because a module along the way had an error processing it. Document readers/writers should
    generally be robust to this and simply pass through the whole thing where possible, so that it's always
    possible to work out, where one of these pops up, where the error occurred.

    """
    class Document:
        def raw_to_internal(self, raw_data):
            if not raw_data.startswith(u"***** EMPTY DOCUMENT *****"):
                raise ValueError(u"tried to read empty document text from invalid text: %s" % raw_data)
            text = raw_data.partition("\n")[2]
            module_line, __, text = text.partition("\n\n")
            module_name = module_line.partition(": ")[2]
            error_info = text.partition("\n")[2]
            return {"module_name": module_name, "error_info": error_info}

        def internal_to_raw(self, internal_data):
            return u"***** EMPTY DOCUMENT *****\nEmpty due to processing error in module: %s\n\n" \
                   u"Full error details:\n%s" % \
                   (internal_data["module_name"], internal_data["error_info"])

        @property
        def module_name(self):
            return self.internal_data["module_name"]

        @property
        def error_info(self):
            return self.internal_data["error_info"]

        def __unicode__(self):
            return self.internal_to_raw(self.internal_data)

        def __str__(self):
            return unicode(self).encode("ascii", "ignore")


def invalid_document(module_name, error_info):
    """
    Convenience function to create an invalid document instance.

    """
    return InvalidDocument()({
        "module_name": module_name,
        "error_info": error_info,
    }, from_internal=True)


def invalid_document_or_text(text):
    """
    If the text represents an invalid document, parse it and return an InvalidDocument object.
    Otherwise, return the text as is.

    """
    if is_invalid_doc(text):
        return text
    elif text.startswith("***** EMPTY DOCUMENT *****"):
        return InvalidDocument()(text)
    else:
        return text


def is_invalid_doc(doc):
    """
    Check whether the given document is of the invalid document types
    """
    return isinstance(doc, DataPointType.Document) and InvalidDocument().is_type_for_doc(doc)


class RawDocumentType(DataPointType):
    """
    Base document type. All document types for grouped corpora should be subclasses of this.

    It may be used itself as well, where documents are just treated as raw data, though most of the time it will
    be appropriate to use subclasses to provide more information and processing operations specific to the
    datatype.

    """
    class Document:
        def raw_to_internal(self, raw_data):
            # Just include the raw data itself, so it's possible to convert back to raw data later
            return {"raw_data": raw_data}

        def internal_to_raw(self, internal_data):
            return internal_data["raw_data"]


class TextDocumentType(RawDocumentType):
    """
    Documents that contain text, most often human-readable documents from a textual
    corpus. Most often used as a superclass for other, more specific, document types.

    This type does not special processing, since the storage format is already a
    unicode string, which is fine for raw text. However, it
    serves to indicate that the document represents text (not just any old raw data).

    The property `text` provides the text, which is, for this base type, just the
    raw data. However, subclasses will override this, since their raw data will
    contain information other than the raw text.

    """
    class Document:
        @property
        def text(self):
            return self.raw_data


class RawTextDocumentType(TextDocumentType):
    """
    Subclass of TextDocumentType used to indicate that the text hasn't been
    processed (tokenized, etc). Note that text that has been tokenized, parsed, etc does
    not use subclasses of this type, so they will not be considered compatible if this type
    is used as a requirement.

    """


class DataPointError(Exception):
    pass
