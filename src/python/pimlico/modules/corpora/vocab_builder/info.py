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
from pimlico.datatypes.dictionary import Dictionary
from pimlico.datatypes.tokenized import TokenizedCorpus


class ModuleInfo(BaseModuleInfo):
    module_type_name = "term_feature_vocab_builder"
    module_readable_name = "Term-feature corpus vocab builder"
    module_inputs = [("text", TokenizedCorpus)]
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
    }
