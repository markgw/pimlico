# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Perform text normalization on tokenized documents.

Currently, this includes only case normalization (to upper or lower case). In
the future, more normalization operations may be added.

.. todo::

   Update to new datatypes system and add test pipeline

"""
from pimlico.core.modules.map import DocumentMapModuleInfo

from pimlico.core.modules.options import choose_from_list
from pimlico.old_datatypes.tar import TarredCorpusType
from pimlico.old_datatypes.tar import TarredCorpusWriter
from pimlico.old_datatypes.tokenized import TokenizedCorpus
from pimlico.old_datatypes.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "normalize"
    module_readable_name = "Normalize tokenized text"
    module_inputs = [("corpus", TarredCorpusType(TokenizedDocumentType))]
    module_outputs = [("corpus", TokenizedCorpus)]
    module_options = {
        "case": {
            "help": "Transform all text to upper or lower case. Choose from 'upper' or 'lower', "
                    "or leave blank to not perform transformation",
            "default": u"",
            "type": choose_from_list(["upper", "lower", ""]),
        },
    }

    def get_writer(self, output_name, output_dir, append=False):
        if output_name == "corpus":
            return TarredCorpusWriter(output_dir, append=append)
