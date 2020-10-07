# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Similar to :mod:`~pimlico.modules.corpora.split`, but instead of taking a random split of the dataset, splits it
according to a given list of documents, putting those in the list in one set and the rest in another.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.core import StringList
from pimlico.datatypes.corpora import GroupedCorpus
from pimlico.datatypes.corpora.grouped import GroupedCorpusWithTypeFromInput


class ModuleInfo(BaseModuleInfo):
    module_type_name = "list_filter"
    module_readable_name = "Corpus document list filter"
    module_inputs = [("corpus", GroupedCorpus()), ("list", StringList())]
    module_outputs = [("set1", GroupedCorpusWithTypeFromInput()), ("set2", GroupedCorpusWithTypeFromInput())]
    module_options = {}
    module_supports_python2 = True
