# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Trains LDA using Gensim's `basic LDA implementation <https://radimrehurek.com/gensim/models/ldamodel.html>`_,
or `the multicore version <https://radimrehurek.com/gensim/models/ldamulticore.html>`_.

.. todo::

   Add test pipeline and test

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import str_to_bool, comma_separated_strings, opt_type_help
from pimlico.datatypes import GensimLdaModel, GroupedCorpus, Dictionary
from pimlico.datatypes.corpora.ints import IntegerListsDocumentType


@opt_type_help("'symmetric', 'asymmetric', 'auto' or a float")
def alpha_opt(val):
    if val not in ["symmetric", "asymmetric", "auto"]:
        # If not one of these, should be a single float or a list of floats
        if "," in val:
            # List of floats
            val = [float(v) for v in val.split(",")]
        else:
            val = float(val)
    return val


@opt_type_help("'symmetric', 'auto' or a float")
def eta_opt(val):
    if val not in ["symmetric", "auto"]:
        val = float(val)
    return val


class ModuleInfo(BaseModuleInfo):
    module_type_name = "lda_trainer"
    module_readable_name = "LDA trainer"
    module_inputs = [("corpus", GroupedCorpus(IntegerListsDocumentType())), ("vocab", Dictionary())]
    module_outputs = [("model", GensimLdaModel())]
    module_options = {
        "ignore_terms": {
            "type": comma_separated_strings,
            "default": [],
            "help": "Ignore any of these terms in the bags of words when iterating over the corpus to train the "
                    "model. Typically, you'll want to include an OOV term here if your corpus has one, and any "
                    "other special terms that are not part of a document's content"
        },
        "tfidf": {
            "type": str_to_bool,
            "default": False,
            "help": "Transform word counts using TF-IDF when presenting documents to the model for training. "
                    "Default: False",
        },
        "multicore": {
            "type": str_to_bool,
            "default": False,
            "help": "Use Gensim's multicore implementation of LDA training (gensim.models.ldamulticore). Default "
                    "is to use gensim.models.ldamodel. Number of cores used for training set by Pimlico's processes "
                    "parameter",
        },
        "num_topics": {
            "type": int,
            "default": 100,
            "help": "Number of topics for the trained model to have. Default: 100"
        },
        "distributed": {
            "type": str_to_bool,
            "default": False,
            "help": "Turn on distributed computing. Default: False. Ignored by multicore implementation",
        },
        "chunksize": {
            "type": int,
            "default": 2000,
            "help": "Model's chunksize parameter. Chunk size to use for distributed/multicore computing. Default: 2000",
        },
        "passes": {
            "type": int,
            "default": 1,
            "help": "Passes parameter. Default: 1",
        },
        "update_every": {
            "type": int,
            "default": 1,
            "help": "Model's update_every parameter. Default: 1. Ignored by multicore implementation",
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
