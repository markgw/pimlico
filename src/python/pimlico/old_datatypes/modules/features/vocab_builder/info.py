# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.old_datatypes.dictionary import Dictionary
from pimlico.old_datatypes.features import TermFeatureListDocumentType
from pimlico.old_datatypes.tar import TarredCorpusType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "term_feature_vocab_builder"
    module_readable_name = "Term-feature corpus vocab builder"
    module_inputs = [("term_features", TarredCorpusType(TermFeatureListDocumentType))]
    module_outputs = [("term_vocab", Dictionary), ("feature_vocab", Dictionary)]
    module_options = {
        "term_threshold": {
            "help": "Minimum number of occurrences required of a term to be included",
            "type": int,
        },
        "term_max_prop": {
            "help": "Include terms that occur in max this proportion of documents",
            "type": float,
        },
        "term_limit": {
            "help": "Limit vocab size to this number of most common entries (after other filters)",
            "type": int,
        },
        "feature_threshold": {
            "help": "Minimum number of occurrences required of a feature to be included",
            "type": int,
        },
        "feature_max_prop": {
            "help": "Include features that occur in max this proportion of documents",
            "type": float,
        },
        "feature_limit": {
            "help": "Limit vocab size to this number of most common entries (after other filters)",
            "type": int,
        },
    }
    module_supports_python2 = True
