# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Text normalization for raw text documents.

Similar to :mod:`~pimlico.modules.text.normalize` module, but operates on raw text,
not pre-tokenized text, so provides a slightly different set of tools.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo

from pimlico.core.modules.options import choose_from_list, str_to_bool
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import TextDocumentType, RawTextDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "text_normalize"
    module_readable_name = "Normalize raw text"
    module_inputs = [("corpus", GroupedCorpus(TextDocumentType()))]
    module_outputs = [("corpus", GroupedCorpus(RawTextDocumentType()))]
    module_options = {
        "case": {
            "help": "Transform all text to upper or lower case. Choose from 'upper' or 'lower', "
                    "or leave blank to not perform transformation",
            "default": u"",
            "type": choose_from_list(["upper", "lower", ""]),
        },
        "strip": {
            "help": "Strip whitespace from the start and end of lines",
            "type": str_to_bool,
        },
        "blank_lines": {
            "help": "Remove all blank lines (after whitespace stripping, if requested)",
            "type": str_to_bool,
        },
    }
    module_supports_python2 = True
