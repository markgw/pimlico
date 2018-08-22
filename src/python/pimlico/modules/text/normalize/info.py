# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Perform text normalization on tokenized documents.

Currently, this includes only the following:

 - case normalization (to upper or lower case)
 - blank line removal
 - empty sentence removal

In the future, more normalization operations may be added.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo

from pimlico.core.modules.options import choose_from_list, str_to_bool
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "normalize"
    module_readable_name = "Normalize tokenized text"
    module_inputs = [("corpus", GroupedCorpus(TokenizedDocumentType()))]
    module_outputs = [("corpus", GroupedCorpus(TokenizedDocumentType()))]
    module_options = {
        "case": {
            "help": "Transform all text to upper or lower case. Choose from 'upper' or 'lower', "
                    "or leave blank to not perform transformation",
            "default": u"",
            "type": choose_from_list(["upper", "lower", ""]),
        },
        "remove_empty": {
            "help": "Skip over any empty sentences (i.e. blank lines)",
            "default": False,
            "type": str_to_bool,
        },
        "remove_only_punct": {
            "help": "Skip over any sentences that are empty if punctuation is ignored",
            "default": False,
            "type": str_to_bool,
        },
    }

