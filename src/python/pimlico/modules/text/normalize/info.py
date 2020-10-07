# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Perform text normalization on tokenized documents.

Currently, this includes the following:

 - case normalization (to upper or lower case)
 - blank line removal
 - empty sentence removal
 - punctuation removal
 - removal of words that contain only punctuation
 - numerical character removal
 - minimum word length filter

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
            "help": "Skip over any empty sentences (i.e. blank lines). Applied after other processing, so this "
                    "will remove sentences that are left empty by other filters",
            "default": False,
            "type": str_to_bool,
        },
        "remove_only_punct": {
            "help": "Skip over any sentences that are empty if punctuation is ignored",
            "default": False,
            "type": str_to_bool,
        },
        "remove_punct": {
            "help": "Remove punctuation from all tokens and then remove the whole token if nothing's left",
            "default": False,
            "type": str_to_bool,
        },
        "remove_nums": {
            "help": "Remove numeric characters",
            "default": False,
            "type": str_to_bool,
        },
        "min_word_length": {
            "help": "Remove any words shorter than this. Default: 0 (don't do anything)",
            "default": 0,
            "type": int,
        },
    }
    module_supports_python2 = True

