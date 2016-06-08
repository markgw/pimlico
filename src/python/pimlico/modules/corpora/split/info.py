# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Split a tarred corpus into two subsets. Useful for dividing a dataset into training and test subsets.
The output datasets have the same type as the input. The documents to put in each set are selected randomly.
Running the module multiple times will give different splits.

Note that you can use this multiple times successively to split more than two ways. For example, say you wanted
a training set with 80% of your data, a dev set with 10% and a test set with 10%, split it first into training
and non-training 80-20, then split the non-training 50-50 into dev and test.

The module also outputs a list of the document names that were included in the first set. Optionally, it outputs
the same thing for the second input too. Note that you might prefer to only store this list for the smaller set:
e.g. in a training-test split, store only the test document list, as the training list will be much larger. In such
a case, just put the smaller set first and don't request the optional output `doc_list2`.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.base import DynamicOutputDatatype, StringList
from pimlico.datatypes.tar import TarredCorpus


class TypeFromInput(DynamicOutputDatatype):
    datatype_name = "same as input corpus"

    def get_datatype(self, module_info):
        return module_info.get_input_datatype("corpus")


class ModuleInfo(BaseModuleInfo):
    module_type_name = "subset"
    module_readable_name = "Corpus subset"
    module_inputs = [("corpus", TarredCorpus)]
    module_outputs = [("set1", TypeFromInput()), ("set2", TypeFromInput()), ("doc_list1", StringList)]
    module_optional_outputs = [("doc_list2", StringList)]
    module_options = {
        "set1_size": {
            "help": "Proportion of the corpus to put in the first set, float between 0.0 and 1.0. Default: 0.2",
            "type": float,
            "default": 0.2,
        },
    }
