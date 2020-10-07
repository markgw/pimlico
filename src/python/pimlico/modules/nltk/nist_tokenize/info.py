# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Sentence splitting and tokenization using the
`NLTK NIST tokenizer <https://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.nist>`_.

Very simple tokenizer that's fairly language-independent and doesn't need
a trained model. Use this if you just need a rudimentary tokenization
(though more sophisticated than :mod:`~pimlico.modules.text.simple_tokenize`).

"""

from pimlico.core.dependencies.python import nltk_dependency, NLTKResource
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import RawTextDocumentType
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "nltk_nist_tokenizer"
    module_readable_name = "NIST tokenizer"
    module_inputs = [("text", GroupedCorpus(RawTextDocumentType()))]
    module_outputs = [("documents", GroupedCorpus(TokenizedDocumentType()))]
    module_options = {
        "lowercase": {
            "help": "Lowercase all output. Default: False",
            "type": str_to_bool,
            "default": False,
        },
        "non_european": {
            "help": "Use the tokenizer's international_tokenize() method instead of tokenize(). Default: False",
            "type": str_to_bool,
            "default": False,
        },
    }
    module_supports_python2 = True

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [
            nltk_dependency,
            NLTKResource("perluniprops"),
        ]
