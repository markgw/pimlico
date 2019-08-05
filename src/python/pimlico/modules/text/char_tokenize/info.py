# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Filter to treat text data as character-level tokenized data. This makes it simple to
train character-level models, since the output appears exactly like a tokenized
document, where each token is a single character. You can then feed it into any
module that expects tokenized text.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import TextDocumentType
from pimlico.datatypes.corpora.tokenized import CharacterTokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "char_tokenize"
    module_readable_name = "Text to character level"
    module_inputs = [("corpus", GroupedCorpus(TextDocumentType()))]
    module_outputs = [("corpus", GroupedCorpus(CharacterTokenizedDocumentType()))]
    module_options = {}
