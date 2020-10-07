# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Trains DTM using Gensim's `DTM implementation <https://radimrehurek.com/gensim/models/ldaseqmodel.html>`_.

Documents in the input corpus should be accompanied by an aligned corpus
of string labels, where each time slice is represented by a label. The
slices should be ordered, so all instances of a given label should be
in sequence.

"""
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import comma_separated_strings, str_to_bool
from pimlico.datatypes import GroupedCorpus, Dictionary
from pimlico.datatypes.corpora.ints import IntegerListsDocumentType
from pimlico.datatypes.corpora.strings import LabelDocumentType
from pimlico.datatypes.gensim import GensimLdaSeqModel


class ModuleInfo(BaseModuleInfo):
    module_type_name = "ldaseq_trainer"
    module_readable_name = "LDA-seq (DTM) trainer"
    module_inputs = [
        ("corpus", GroupedCorpus(IntegerListsDocumentType())),
        ("labels", GroupedCorpus(LabelDocumentType())),
        ("vocab", Dictionary())
    ]
    module_outputs = [("model", GensimLdaSeqModel())]
    module_options = {
        "alphas": {
            "type": float,
            "default": 0.01,
            "help": "The prior probability for the model"
        },
        "ignore_terms": {
            "type": comma_separated_strings,
            "default": [],
            "help": "Ignore any of these terms in the bags of words when iterating over the corpus to train the "
                    "model. Typically, you'll want to include an OOV term here if your corpus has one, and any "
                    "other special terms that are not part of a document's content"
        },
        "num_topics": {
            "type": int,
            "default": 100,
            "help": "Number of topics for the trained model to have. Default: 100"
        },
        "chain_variance": {
            "type": float,
            "default": 0.005,
            "help": "Gaussian parameter defined in the beta distribution "
                    "to dictate how the beta values evolve over time."
        },
        "chunksize": {
            "type": int,
            "default": 100,
            "help": "Model's chunksize parameter. Chunk size to use for "
                    "distributed/multicore computing. Default: 2000."
        },
        "passes": {
            "type": int,
            "default": 10,
            "help": "Number of passes over the corpus for the initial LDA model. Default: 10"
        },
        "lda_inference_max_iter": {
            "type": int,
            "default": 25,
            "help": "Maximum number of iterations in the inference step of the LDA training. Default: 25"
        },
        "em_min_iter": {
            "type": int,
            "default": 6,
            "help": "Minimum number of iterations until converge of the Expectation-Maximization algorithm"
        },
        "em_max_iter": {
            "type": int,
            "default": 20,
            "help": "Maximum number of iterations until converge of the Expectation-Maximization algorithm"
        },
        "tfidf": {
            "type": str_to_bool,
            "default": False,
            "help": "Transform word counts using TF-IDF when presenting documents to the model for training. "
                    "Default: False",
        },
    }
    module_supports_python2 = False
