# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""Some basic statistics about tokenized corpora

Counts the number of tokens, sentences and distinct tokens in a corpus.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import GroupedCorpus, NamedFile
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "corpus_stats"
    module_readable_name = "Corpus statistics"
    module_inputs = [("corpus", GroupedCorpus(TokenizedDocumentType()))]
    module_outputs = [("stats", NamedFile("stats.json"))]
    module_supports_python2 = True
