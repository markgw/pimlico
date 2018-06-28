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

from pimlico.old_datatypes.documents import TextDocumentType
from pimlico.old_datatypes.tar import TarredCorpusType, tarred_corpus_with_data_point_type
from pimlico.old_datatypes.tokenized import CharacterTokenizedDocumentType, CharacterTokenizedCorpusWriter


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "char_tokenize"
    module_readable_name = "Text to character level"
    module_inputs = [("corpus", TarredCorpusType(TextDocumentType))]
    module_outputs = [("corpus", tarred_corpus_with_data_point_type(CharacterTokenizedDocumentType))]
    module_options = {}

    def get_writer(self, output_name, output_dir, append=False):
        if output_name == "corpus":
            return CharacterTokenizedCorpusWriter(output_dir, append=append)
