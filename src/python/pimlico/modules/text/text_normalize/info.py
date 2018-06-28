# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Text normalization for raw text documents.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo

from pimlico.core.modules.options import choose_from_list, str_to_bool
from pimlico.old_datatypes.documents import TextDocumentType
from pimlico.old_datatypes.tar import TarredCorpusType, RawTextTarredCorpus
from pimlico.old_datatypes.tar import TarredCorpusWriter


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "text_normalize"
    module_readable_name = "Normalize raw text"
    module_inputs = [("corpus", TarredCorpusType(TextDocumentType))]
    module_outputs = [("corpus", RawTextTarredCorpus)]
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

    def get_writer(self, output_name, output_dir, append=False):
        if output_name == "corpus":
            return TarredCorpusWriter(output_dir, append=append)
