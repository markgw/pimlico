# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""Extract NP chunks

Performs the full spaCy pipeline including tokenization, sentence
segmentation, POS tagging and parsing and outputs documents containing
only a list of the noun phrase chunks that were found by the parser.

This functionality is provided very conveniently by spaCy's ``Doc.noun_chunks``
after parsing, so this is a light wrapper around spaCy.

The output is presented as a tokenized document. Each sentence in the
document represents a single NP.

"""
from pimlico.core.dependencies.python import spacy_dependency
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import RawTextDocumentType
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "spacy_extract_nps"
    module_readable_name = "NP chunk extractor"
    module_inputs = [("text", GroupedCorpus(RawTextDocumentType()))]
    module_outputs = [("nps", GroupedCorpus(TokenizedDocumentType()))]
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
