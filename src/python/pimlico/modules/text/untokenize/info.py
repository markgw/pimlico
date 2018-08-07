# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Filter to take tokenized text and join it together to make raw text.

This module shouldn't be necessary and will be removed later. For the time
being, it's here as a workaround for [this problem](https://github.com/markgw/pimlico/issues/1#issuecomment-383620759),
until it's solved in the datatype redesign.

Tokenized text is a subtype of text, so theoretically it should be acceptable to modules
that expect plain text (and is considered so by typechecking). But it provides an incompatible
data structure, so things go bad if you use it like that.

.. todo::

   Update to new datatypes system and add test pipeline

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.old_datatypes.tar import TarredCorpusWriter
from pimlico.old_datatypes.documents import TextDocumentType
from pimlico.old_datatypes.tar import TarredCorpusType, tarred_corpus_with_data_point_type
from pimlico.old_datatypes.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "untokenize"
    module_readable_name = "Tokenized text to text"
    module_inputs = [("corpus", TarredCorpusType(TokenizedDocumentType))]
    module_outputs = [("corpus", tarred_corpus_with_data_point_type(TextDocumentType))]
    module_options = {
        "joiner": {
            "help": "String to join words on. (Default: space)",
            "default": u" ",
            "type": unicode,
        },
        "sentence_joiner": {
            "help": "String to join lines/sentences on. (Default: linebreak)",
            "default": u"\n",
            "type": unicode,
        },
    }

    def get_writer(self, output_name, output_dir, append=False):
        if output_name == "corpus":
            return TarredCorpusWriter(output_dir, append=append)
