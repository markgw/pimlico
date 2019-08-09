# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Document types used to represent datatypes of individual documents in an IterableCorpus or subtype.

"""
from traceback import format_exc

from builtins import object
from future.utils import with_metaclass

__all__ = ["DataPointType", "RawDocumentType", "TextDocumentType", "RawTextDocumentType", "DataPointError",
           "InvalidDocument"]


class DataPointTypeMeta(type):
    """
    Metaclass for all data point type classes. Takes care of preparing a
    Document class for every datatype.

    You should never need to do anything with this: it's used by the base datatype,
    and hence by every other datatype.

    """
    def __new__(cls, *args, **kwargs):
        new_cls = super(DataPointTypeMeta, cls).__new__(cls, *args, **kwargs)
        # Replace the existing Document class, if any, which is used to construct the actual Document,
        # with the constructed Document
        new_cls.Document = DataPointTypeMeta._get_document_cls(new_cls)
        return new_cls

    @staticmethod
    def _get_document_cls(cls):
        # Cache document subtyping, so that the same type object is returned from repeated calls on the
        # same document type
        if not hasattr(cls, "__document_type"):
            if len(cls.__bases__) == 0 or cls.__bases__[0] is object:
                # On the base class, we just return the base document
                cls.__document_type = cls.Document
            else:
                parent_doc_cls = cls.__bases__[0].Document
                my_doc_cls = cls.Document
                if my_doc_cls is parent_doc_cls:
                    # Nothing overridden
                    new_dict = {}
                else:
                    new_dict = dict(my_doc_cls.__dict__)

                # Don't inherit the __dict__ and __weakref__ attributes
                # These will be created on the new type as necessary
                if "__dict__" in new_dict:
                    del new_dict["__dict__"]
                if "__weakref__" in new_dict:
                    del new_dict["__weakref__"]

                # Perform subclassing so that a new Document is created that is a subclass of the parent's document
                cls.__document_type = type("Document", (parent_doc_cls,), new_dict)
        return cls.__document_type


class DataPointType(with_metaclass(DataPointTypeMeta, object)):
    """
    Base data-point type for iterable corpora. All iterable corpora should have data-point types that are
    subclasses of this.

    Every data point type has a corresponding document class, which can be accessed as
    `MyDataPointType.Document`. When overriding data point types, you can define a nested
    `Document` class, with no base class, to override parts of the document class'
    functionality or add new methods, etc. This will be used to automatically create
    the `Document` class for the data point type.

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
    #: Metadata keys that should be written for this data point type, with default values and
    #: strings documenting the meaning of the parameter. Used for writers for this data point
    #: type. See :class:`~pimlico.datatypes.PimlicoDatatype.Writer`.
    metadata_defaults = {}

    def __init__(self):
        # This is set when the reader is initialized
        self.metadata = None

    def __call__(self, **kwargs):
        """
        Produce a document of this type. Data is specified using kwargs, which should
        be keys listed in the document type's `keys` list.

        If `raw_data` is given it should be a string.
        Other kwargs are ignored and the document is instantiated
        from the raw data alone. Otherwise, it is instantiated from an internal data
        dictionary containing all of the specified keys.

        """
        if "raw_data" in kwargs:
            raw_data = kwargs["raw_data"]
            internal_data = None
        else:
            if set(kwargs.keys()) != set(self.Document.keys):
                # Check that no unknown keys are given for the document's internal representation
                unknown_keys = set(kwargs.keys()) - set(self.Document.keys)
                if unknown_keys:
                    raise DocumentInitializationError("{} got unknown key(s) {} to create a document".format(
                        self.name, ", ".join("'{}'".format(k) for k in sorted(unknown_keys))
                    ))
                # Check that all required keys are given
                missing_keys = set(self.Document.keys) - set(kwargs.keys())
                if missing_keys:
                    raise DocumentInitializationError("{} requires key(s) {} to create a document, only got {}".format(
                        self.name,
                        ", ".join("'{}'".format(k) for k in sorted(missing_keys)),
                        ", ".join("'{}'".format(k) for k in sorted(kwargs.keys()))
                    ))
            raw_data = None
            internal_data = dict(kwargs)

        return self.Document(self, raw_data=raw_data, internal_data=internal_data)

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

    def reader_init(self, reader):
        """
        Called when a reader is initialized. May be overridden to perform any tasks
        specific to the data point type that need to be done before the reader
        starts producing data points.

        The super `reader_init()` should be called. This takes care of making
        reader metadata available in the `metadata` attribute of the data point
        type instance.

        """
        self.metadata = reader.metadata

    def writer_init(self, writer):
        """
        Called when a writer is initialized. May be overridden to perform any
        tasks specific to the data point type that should be done before documents
        start getting written.

        The super `writer_init()` should be called. This takes care of updating
        the writer's metadata from anything in the instance's `metadata`
        attribute, for any keys given in the data point type's `metadata_defaults`.

        """
        metadata = self.metadata or {}
        # Don't need to set default values here, as that's handled by the writer
        # Just pass through any metadata values for the data point type's keys
        for key in self.metadata_defaults:
            if key in metadata:
                writer.metadata[key] = metadata[key]

    @classmethod
    def full_class_name(cls):
        """
        The fully qualified name of the class for this data point type,
        by which it is referenced in config files. Used in docs

        """
        return "%s.%s" % (cls.__module__, cls.__name__)

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

        A data point type's constructed document class is available as `MyDataPointType.Document`.

        Each document type should provide a method to convert from raw data (a bytes object in Py3,
        or ``future``'s backport of ``bytes`` in Py2) to the
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
        #: Specifies the keys that a document has in its internal data
        #: Subclasses should specify their keys
        #: The internal data fields corresponding to these can be accessed as attributes of the document
        keys = []

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
                try:
                    # Raw data not available yet: convert from internal data
                    self._raw_data = self.internal_to_raw(self._internal_data)
                    self.raw_available()
                except Exception as e:
                    # Catch any exceptions and wrap them
                    # In particular, it's important to catch attribute errors, as these otherwise lead
                    # to __getatttr__ being called and give mystifying errors
                    raise DataConversionError(
                        "{} error converting internal to raw data for document type {}: {}. [{}]".format(
                            type(e).__name__, self.data_point_type, e, format_exc(),
                        ))
            return self._raw_data

        @property
        def internal_data(self):
            if self._internal_data is None:
                try:
                    # Internal data not available yet: convert from raw
                    self._internal_data = self.raw_to_internal(self._raw_data)
                    self.internal_available()
                except Exception as e:
                    # Catch any exceptions and wrap them
                    raise DataConversionError(
                        "{} error converting raw to internal data for document type {}: {}. [{}]".format(
                            type(e).__name__, self.data_point_type, e, format_exc(),
                        ))
            return self._internal_data

        def __reduce__(self):
            return (_DocumentPickler(), (
                self.data_point_type,
                self._raw_data if self._raw_data is not None else self._internal_data,
                self._raw_data is None
            ))

        def __getattr__(self, item):
            # Provide the internal data keys defined by the doc type as attributes for easy access
            if item in self.keys:
                return self.internal_data[item]
            else:
                raise AttributeError("{} document has no attribute or data key '{}'".format(
                    self.data_point_type.name, item
                ))


class _DocumentPickler(object):
    """
    Our fancy document typing system means pickle has trouble reconstructing document objects.
    We reduce a document instance as the data point type instance, plus either the raw
    data or the internal data (avoiding conversion) and a flag to say which type of data
    it is.

    Then we can simply reconstruct the document from the datatype's __call__ when unpickling.

    """
    def __call__(self, datatype, data, from_internal):
        if from_internal:
            return datatype(**data)
        else:
            return datatype(raw_data=data)


class InvalidDocument(DataPointType):
    """
    Widely used in Pimlico to represent an empty document that is empty not because the original input document
    was empty, but because a module along the way had an error processing it. Document readers/writers should
    generally be robust to this and simply pass through the whole thing where possible, so that it's always
    possible to work out, where one of these pops up, where the error occurred.

    """
    class Document(object):
        keys = ["module_name", "error_info"]

        def raw_to_internal(self, raw_data):
            # Raw data always encoded as utf-8
            raw_data = raw_data.decode("utf-8")

            if not raw_data.startswith(u"***** EMPTY DOCUMENT *****"):
                raise ValueError(u"tried to read empty document text from invalid text: %s" % raw_data)
            text = raw_data.partition("\n")[2]
            module_line, __, text = text.partition("\n\n")
            module_name = module_line.partition(": ")[2]
            error_info = text.partition("\n")[2]
            return {"module_name": module_name, "error_info": error_info}

        def internal_to_raw(self, internal_data):
            # Encode back to utf-8 for the raw data
            return bytes(
                (u"***** EMPTY DOCUMENT *****\nEmpty due to processing error in module: %s\n\n"
                 u"Full error details:\n%s" %
                 (internal_data["module_name"], internal_data["error_info"])).encode("utf-8")
            )

        @property
        def module_name(self):
            return self.internal_data["module_name"]

        @property
        def error_info(self):
            return self.internal_data["error_info"]

        def __unicode__(self):
            return self.raw_data.decode("utf-8")

        def __str__(self):
            return self.raw_data

        def __repr__(self):
            return "InvalidDocument()"


def invalid_document(module_name, error_info):
    """
    Convenience function to create an invalid document instance.

    """
    return InvalidDocument()(module_name=module_name, error_info=error_info)


def invalid_document_or_raw(data):
    """
    Takes the given raw data, given as a bytes object, and returns it as an
    InvalidDocument object, if it represents an invalid document, or returns
    the data as is otherwise.

    """
    is_invalid = False
    try:
        if data.startswith(b"***** EMPTY DOCUMENT *****"):
            # This is the raw data for an invalid doc
            is_invalid = True
    except TypeError:
        if not isinstance(data, bytes):
            raise DataConversionError("invalid_document_or_raw() should be given a bytes object, "
                                      "not {}".format(type(data).__name__))
        else:
            raise

    if is_invalid:
        return InvalidDocument()(raw_data=data)
    else:
        return data


# Alias for backwards compatibility
# Doesn't any longer correctly describe the function
def invalid_document_or_text(module_name, data):
    return invalid_document_or_raw(data)


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
    class Document(object):
        keys = ["raw_data"]

        def raw_to_internal(self, raw_data):
            # Just include the raw data itself, so it's possible to convert back to raw data later
            return {"raw_data": raw_data.decode("utf-8")}

        def internal_to_raw(self, internal_data):
            return bytes(internal_data["raw_data"].encode("utf-8"))


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
    class Document(object):
        keys = ["text"]

        def internal_to_raw(self, internal_data):
            return bytes(internal_data["text"].encode("utf-8"))

        def raw_to_internal(self, raw_data):
            return {"text": raw_data.decode("utf-8")}


class RawTextDocumentType(TextDocumentType):
    """
    Subclass of TextDocumentType used to indicate that the text hasn't been
    processed (tokenized, etc). Note that text that has been tokenized, parsed, etc does
    not use subclasses of this type, so they will not be considered compatible if this type
    is used as a requirement.

    """


class DataPointError(Exception):
    pass


class DataConversionError(Exception):
    pass


class DocumentInitializationError(Exception):
    pass
