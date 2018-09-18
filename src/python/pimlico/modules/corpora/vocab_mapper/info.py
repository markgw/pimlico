# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
.. todo::

   Write description of vocab mapper module

.. todo::

   Add test pipeline and test

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes import GroupedCorpus, Dictionary
from pimlico.datatypes.corpora.ints import IntegerListsDocumentType
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "vocab_mapper"
    module_readable_name = "Tokenized corpus to ID mapper"
    module_inputs = [("text", GroupedCorpus(TokenizedDocumentType())), ("vocab", Dictionary())]
    module_outputs = [("ids", GroupedCorpus(IntegerListsDocumentType()))]
    module_options = {
        "oov": {
            "help": "If given, special token to map all OOV tokens to. Otherwise, use vocab_size+1 as index. "
                    "Special value 'skip' simply skips over OOV tokens",
        },
    }
