# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Tokenization using spaCy.

"""
from pimlico.core.dependencies.python import spacy_dependency
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import TextDocumentType
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "spacy_tokenizer"
    module_readable_name = "Tokenizer"
    module_inputs = [("text", GroupedCorpus(TextDocumentType()))]
    module_outputs = [("documents", GroupedCorpus(TokenizedDocumentType()))]
    module_options = {
        "model": {
            "help": "spaCy model to use. This may be a name of a standard spaCy model or a path to the "
                    "location of a trained model on disk, if on_disk=T. "
                    "If it's not a path, the spaCy download command will be run before execution",
            "default": "en_core_web_sm",
        },
        "on_disk": {
            "help": "Load the specified model from a location on disk (the model parameter gives the path)",
            "type": str_to_bool,
        }
    }
    module_supports_python2 = True

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [spacy_dependency]
