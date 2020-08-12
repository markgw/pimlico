"""
Documents consisting of strings.

.. seealso::

   :class:`~pimlico.datatypes.corpora.TextDocumentType` and
   :class:`~pimlico.datatypes.corpora.RawTextDocumentType`: basic text
   (i.e. unicode string) document types for normal textual documents.

"""
from pimlico.datatypes.corpora.data_points import RawDocumentType

__all__ = ["LabelDocumentType"]


class LabelDocumentType(RawDocumentType):
    """
    Simple document type for storing a short label associated with a document.

    Identical to :class:`~pimlico.datatypes.corpora.TextDocumentType`,
    but distinguished for typechecking, so that only corpora designed to be
    used as short labels can be used as input where a label corpus is required.

    The string label is stored in the ``label`` attribute.

    """
    class Document(object):
        keys = ["label"]

        def internal_to_raw(self, internal_data):
            return bytes(internal_data["label"].encode("utf-8"))

        def raw_to_internal(self, raw_data):
            return {"label": raw_data.decode("utf-8")}
