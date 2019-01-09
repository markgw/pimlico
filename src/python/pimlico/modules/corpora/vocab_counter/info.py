# coding=utf-8
# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
u"""
Count the frequency of each token of a vocabulary in a given corpus (most often
the corpus on which the vocabulary was built).

Note that this distribution is not otherwise available along with the vocabulary.
It stores the document frequency counts – how many documents each token appears
in – which may sometimes be a close enough approximation to the actual frequencies.
But, for example, when working with character-level tokens, this estimate will
be very poor.

The output will be a 1D array whose size is the length of the vocabulary, or
the length plus one, if ``oov_excluded=T`` (used if the corpus has been mapped
so that OOVs are represented by the ID ``vocab_size+1``, instead of having a
special token).

"""
from pimlico.core.dependencies.python import numpy_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import GroupedCorpus, Dictionary
from pimlico.datatypes.arrays import NumpyArray
from pimlico.datatypes.corpora.ints import IntegerListsDocumentType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "vocab_counter"
    module_readable_name = "Token frequency counter"
    module_inputs = [("corpus", GroupedCorpus(IntegerListsDocumentType())), ("vocab", Dictionary())]
    module_outputs = [("distribution", NumpyArray())]
    module_options = {
        "oov_excluded": {
            "help": "Indicates that the corpus has been mapped so that OOVs are represented "
                    "by the ID vocab_size+1, instead of having a special token in the vocab",
            "type": str_to_bool,
        },
    }

    def get_software_dependencies(self):
        return [numpy_dependency] + super(ModuleInfo, self).get_software_dependencies()
