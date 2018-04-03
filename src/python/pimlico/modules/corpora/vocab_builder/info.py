# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Builds a dictionary (or vocabulary) for a tokenized corpus. This is a data structure that assigns an integer
ID to every distinct word seen in the corpus, optionally applying thresholds so that some words are left out.

Similar to :mod:`pimlico.modules.features.vocab_builder`, which builds two vocabs, one for terms and one for
features.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import comma_separated_strings
from pimlico.datatypes.dictionary import Dictionary
from pimlico.datatypes.tar import TarredCorpusType
from pimlico.datatypes.tokenized import TokenizedDocumentType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "vocab_builder"
    module_readable_name = "Corpus vocab builder"
    module_inputs = [("text", TarredCorpusType(TokenizedDocumentType))]
    module_outputs = [("vocab", Dictionary)]
    module_options = {
        "threshold": {
            "help": "Minimum number of occurrences required of a term to be included",
            "type": int,
        },
        "max_prop": {
            "help": "Include terms that occur in max this proportion of documents",
            "type": float,
        },
        "limit": {
            "help": "Limit vocab size to this number of most common entries (after other filters)",
            "type": int,
        },
        "include": {
            "help": "Ensure that certain words are always included in the vocabulary, even if they don't make it "
                    "past the various filters, or are never seen in the corpus. Give as a comma-separated list",
            "type": comma_separated_strings,
        },
        "oov": {
            "help": "Use the final index the represent chars that will be out of vocabulary after applying "
                    "threshold/limit filters. Applied even if the count is 0. "
                    "Represent OOVs using the given string in the vocabulary",
            "type": str,
        },
    }
