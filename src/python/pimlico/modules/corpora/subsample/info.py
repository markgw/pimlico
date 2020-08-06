# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Randomly subsample documents of a corpus at a given rate to create a smaller corpus.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.grouped import CorpusWithTypeFromInput


class ModuleInfo(BaseModuleInfo):
    module_type_name = "subsample"
    module_readable_name = "Random subsample"
    module_inputs = [("corpus", GroupedCorpus())]
    module_outputs = [("corpus", CorpusWithTypeFromInput())]
    module_options = {
        "p": {
            "help": "Probability of including any given document. The resulting corpus will be roughly "
                    "this proportion of the size of the input. Alternatively, you can specify an integer, "
                    "which will be interpreted as the target size of the output. A p value will be calculated "
                    "based on the size of the input corpus",
            "type": float,
            "required": True,
            "example": "0.1",
        },
        "skip_invalid": {
            "help": "Skip over any invalid documents so that the output subset contains just valid document "
                    "and no invalid ones. By default, invalid documents are passed through",
            "type": str_to_bool,
        },
        "seed": {
            "help": "Random seed. We always set a random seed before starting to ensure some level of reproducability",
            "type": int,
            "default": 1234,
        },
    }
    module_supports_python2 = True
