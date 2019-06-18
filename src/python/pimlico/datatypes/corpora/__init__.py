from __future__ import absolute_import

from pimlico.datatypes.corpora.data_points import DataPointType, InvalidDocument, is_invalid_doc, \
    invalid_document_or_text, invalid_document
from .base import IterableCorpus
from .grouped import GroupedCorpus
from . import data_points
from . import tokenized
from . import floats
from . import ints
from . import json
from . import table

"""
This list collects together all the built-in data point types. These can be specified 
using only their class name, rather than requiring a fully-qualified path, when giving 
a data point type in a config file
"""
DATA_POINT_TYPES = [
    data_points.RawDocumentType,
    data_points.RawTextDocumentType, data_points.TextDocumentType,
    tokenized.TokenizedDocumentType, tokenized.CharacterTokenizedDocumentType, tokenized.SegmentedLinesDocumentType,
    floats.FloatListDocumentType, floats.FloatListDocumentType, floats.VectorDocumentType,
    ints.IntegerListsDocumentType, ints.IntegerListDocumentType,
    json.JsonDocumentType,
    table.IntegerTableDocumentType,
]
