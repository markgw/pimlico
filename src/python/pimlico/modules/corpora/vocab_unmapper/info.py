# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Maps all the IDs in an integer lists corpus to their corresponding words
in a vocabulary, producing a tokenized textual corpus.

This is the inverse of :mod:`~pimlico.modules.corpora.vocab_mapper`, which
maps words to IDs. Typically, the resulting integer IDs are used for model
training, but sometimes we need to map in the opposite direction.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes import GroupedCorpus, Dictionary
from pimlico.datatypes.corpora.ints import IntegerListsDocumentType
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "vocab_unmapper"
    module_readable_name = "ID to tokenized corpus mapper"
    module_inputs = [("ids", GroupedCorpus(IntegerListsDocumentType())), ("vocab", Dictionary())]
    module_outputs = [("text", GroupedCorpus(TokenizedDocumentType()))]
    module_options = {
        "oov": {
            "help": "If given, assume the vocab_size+1 was used to represent out-of-vocabulary "
                    "words and map this index to the given token. "
                    "Special value 'skip' simply skips over vocab_size+1 indices",
        },
    }
