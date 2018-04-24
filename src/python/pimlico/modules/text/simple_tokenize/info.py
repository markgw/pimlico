# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Tokenize raw text using simple splitting.

This is useful where either you don't mind about the quality of the tokenization and
just want to test something quickly, or text is actually already tokenized, but stored
as a raw text datatype.

If you want to do proper tokenization, consider either the CoreNLP or OpenNLP core
modules.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.documents import TextDocumentType
from pimlico.datatypes.tar import TarredCorpusType, tarred_corpus_with_data_point_type
from pimlico.datatypes.tokenized import TokenizedDocumentType, TokenizedCorpusWriter


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "simple_tokenize"
    module_readable_name = "Simple tokenization"
    module_inputs = [("corpus", TarredCorpusType(TextDocumentType))]
    module_outputs = [("corpus", tarred_corpus_with_data_point_type(TokenizedDocumentType))]
    module_options = {
        "splitter": {
            "help": "Character or string to split on. Default: space",
            "default": u" ",
            "type": unicode,
        },
    }

    def get_writer(self, output_name, output_dir, append=False):
        if output_name == "corpus":
            return TokenizedCorpusWriter(output_dir, append=append)
