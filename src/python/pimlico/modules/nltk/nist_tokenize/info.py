# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Sentence splitting and tokenization using the
`NLTK NIST tokenizer <https://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.nist>`_.

.. todo::

   Update to new datatypes system and add test pipeline

"""

from pimlico.core.dependencies.python import nltk_dependency, NLTKResource
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import RawTextDocumentType
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "nltk_nist_tokenizer"
    module_readable_name = "OpenNLP NIST tokenizer"
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

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [
            nltk_dependency,
            NLTKResource("perluniprops"),
        ]
