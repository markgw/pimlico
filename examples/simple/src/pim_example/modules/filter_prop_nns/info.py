# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""Filter out proper nouns

A simple custom module to demonstrate how to apply custom processing in a
pipeline. It doesn't do anything very valuable, but is here for use in
the example pipeline ``custom_module.conf``.

This module uses a very simple heuristic to remove proper nouns. It simply
removes any words that start with an upper-case letter and are not at the
start of a sentence. Since we take tokenized documents as input, we assume
that sentence splitting has been correctly applied to the input (some
tokenizers don't do that!).

"""
from pimlico.core.modules.map import DocumentMapModuleInfo

from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "filter_prop_nns"
    module_readable_name = "Filter proper nouns"
    module_inputs = [("corpus", GroupedCorpus(TokenizedDocumentType()))]
    module_outputs = [("corpus", GroupedCorpus(TokenizedDocumentType()))]
    module_options = {}
