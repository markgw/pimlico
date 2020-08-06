"""
Datatypes for storing parse trees from constitutency parsers.

.. note::

   Parse tress are temporary implementations that don't actually parse the data, but just split it into
   sentences. That is, they store the raw output from the OpenNLP parser. In future, this should be
   replaced by a generic tree structure storage.

"""
from pimlico.datatypes.corpora.data_points import RawDocumentType

__all__ = ["OpenNLPTreeStringsDocumentType"]


class OpenNLPTreeStringsDocumentType(RawDocumentType):
    """
    The attribute ``trees`` provides a list of strings representing each of the
    trees in the document, usually one per sentence.

    .. todo::

       In future, this should be replaced by a doc type that reads
       in the parse trees and returns a tree data structure.
       For now, you need to load and process the tree strings yourself.

    """
    data_point_type_supports_python2 = True

    class Document(object):
        keys = ["trees"]

        def raw_to_internal(self, raw_data):
            return {"trees": raw_data.decode("utf-8").split("\n\n")}

        def internal_to_raw(self, internal_data):
            return "\n\n".join(internal_data["trees"]).encode("utf-8")
