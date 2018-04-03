# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.dictionary import Dictionary
from pimlico.datatypes.ints import IntegerListsDocumentCorpus, IntegerListsDocumentCorpusWriter
from pimlico.datatypes.tar import TarredCorpusType
from pimlico.datatypes.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "vocab_mapper"
    module_readable_name = "Tokenized corpus to ID mapper"
    module_inputs = [("text", TarredCorpusType(TokenizedDocumentType)), ("vocab", Dictionary)]
    module_outputs = [("ids", IntegerListsDocumentCorpus)]
    module_options = {
        "oov": {
            "help": "If given, special token to map all OOV characters to. Otherwise, use vocab_size+1 as index",
        },
    }

    def get_writer(self, output_name, output_dir, append=False):
        return IntegerListsDocumentCorpusWriter(output_dir, signed=False, bytes=4, append=append)
