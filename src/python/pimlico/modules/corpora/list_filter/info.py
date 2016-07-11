# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Similar to :mod:pimlico.modules.corpora.split, but instead of taking a random split of the dataset, splits it
according to a given list of documents, putting those in the list in one set and the rest in another.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import DynamicOutputDatatype, StringList
from pimlico.datatypes.tar import TarredCorpus


class TypeFromInput(DynamicOutputDatatype):
    datatype_name = "same as input corpus"

    def get_datatype(self, module_info):
        datatype = module_info.get_input_datatype("corpus")
        # If the input datatype emulates another, it is that other that we will produce as output
        if datatype.emulated_datatype is not None:
            datatype = datatype.emulated_datatype
        return datatype


class ModuleInfo(BaseModuleInfo):
    module_type_name = "list_filter"
    module_readable_name = "Corpus document list filter"
    module_inputs = [("corpus", TarredCorpus), ("list", StringList)]
    module_outputs = [("set1", TypeFromInput()), ("set2", TypeFromInput())]
    module_options = {}
