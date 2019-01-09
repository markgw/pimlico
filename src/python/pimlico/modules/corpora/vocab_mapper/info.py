# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Maps all the words in a tokenized textual corpus to integer IDs, storing
just lists of integers in the output.

This is typically done before doing things like training models on textual
corpora. It ensures that a consistent mapping from words to IDs is used
throughout the pipeline. The training modules use this pre-mapped form
of input, instead of performing the mapping as they read the data, because
it is much more efficient if the corpus needs to be iterated over many times,
as is typical in model training.

First use the :mod:`~pimlico.modules.corpora.vocab_builder` module to
construct the word-ID mapping and filter the vocabulary as you wish,
then use this module to apply the mapping to the corpus.

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
