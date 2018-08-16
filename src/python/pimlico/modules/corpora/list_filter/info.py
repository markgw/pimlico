# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Similar to :mod:`~pimlico.modules.corpora.split`, but instead of taking a random split of the dataset, splits it
according to a given list of documents, putting those in the list in one set and the rest in another.

.. todo::

   Updated to new datatypes system. Add test pipeline

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
