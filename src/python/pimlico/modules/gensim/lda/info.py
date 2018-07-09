# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Trains LDA using Gensim's `basic LDA implementation <https://radimrehurek.com/gensim/models/ldamodel.html>`_.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.datatypes.dictionary import Dictionary
from pimlico.datatypes.gensim import GensimLdaModel
from pimlico.datatypes.ints import IntegerListsDocumentType
from pimlico.datatypes.tar import TarredCorpusType


def alpha_opt(val):
    if val not in ["symmetric", "asymmetric", "auto"]:
        # If not one of these, should be a single float or a list of floats
        if "," in val:
            # List of floats
            val = [float(v) for v in val.split(",")]
        else:
            val = float(val)
    return val


def eta_opt(val):
    if val not in ["symmetric", "auto"]:
        val = float(val)
    return val


class ModuleInfo(BaseModuleInfo):
    module_type_name = "lda_trainer"
    module_readable_name = "LDA trainer"
    module_inputs = [("corpus", TarredCorpusType(IntegerListsDocumentType)), ("vocab", Dictionary)]
    module_outputs = [("model", GensimLdaModel)]
    module_options = {
        "num_topics": {
            "type": int,
            "default": 100,
            "help": "Number of topics for the trained model to have. Default: 100"
        },
        "distributed": {
            "type": str_to_bool,
            "default": False,
            "help": "Turn on distributed computing. Default: False",
        },
        "chunksize": {
            "type": int,
            "default": 2000,
            "help": "Model's chunksize parameter. Chunk size to use for distributed computing. Default: 2000",
        },
        "passes": {
            "type": int,
            "default": 1,
            "help": "Passes parameter. Default: 1",
        },
        "update_every": {
            "type": int,
            "default": 1,
            "help": "Model's update_every parameter. Default: 1",
        },
        "alpha": {
            "type": alpha_opt,
            "default": "symmetric",
            "help": "Alpha prior over topic distribution. "
                    "May be one of special values 'symmetric', 'asymmetric' and 'auto', or a single "
                    "float, or a list of floats. Default: symmetric",
        },
        "eta": {
            "type": eta_opt,
            "default": "symmetric",
            "help": "Eta prior of word distribution. May be one of special values 'auto' and 'symmetric', or a float. "
                    "Default: symmetric",
        },
        "decay": {
            "type": float,
            "default": 0.5,
            "help": "Decay parameter. Default: 0.5",
        },
        "offset": {
            "type": float,
            "default": 1.0,
            "help": "Offset parameter. Default: 1.0",
        },
        "eval_every": {
            "type": int,
            "default": 10,
        },
        "iterations": {
            "default": 50,
            "type": int,
            "help": "Max number of iterations in each update. Default: 50",
        },
        "gamma_threshold": {
            "type": float,
            "default": 0.001,
        },
        "minimum_probability": {
            "type": float,
            "default": 0.01,
        },
        "minimum_phi_value": {
            "type": float,
            "default": 0.01,
        },
    }
