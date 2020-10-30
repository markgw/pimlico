# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
Train GloVe embeddings on a tokenized corpus.

Uses the `original GloVe code <https://github.com/stanfordnlp/GloVe>`, called in a subprocess.

"""
from pimlico.modules.embeddings.glove.datatypes import GloveOutput

from pimlico.core.dependencies.python import numpy_dependency

from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import choose_from_list, str_to_bool
from pimlico.datatypes import GroupedCorpus, Embeddings
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType
from .deps import glove_dependency


class ModuleInfo(BaseModuleInfo):
    module_type_name = "glove"
    module_readable_name = "GloVe embedding trainer"
    module_inputs = [("text", GroupedCorpus(TokenizedDocumentType()))]
    module_outputs = [("embeddings", Embeddings()), ("glove_output", GloveOutput())]
    module_options = {
        "max_vocab": {
            "help": "Upper bound on vocabulary size, i.e. keep the <max_vocab> most frequent words. "
                    "The minimum frequency words are randomly sampled so as to obtain an even distribution "
                    "over the alphabet. Default: 0 (no limit)",
            "type": int,
            "default": 0,
        },
        "min_count": {
            "help": "Lower limit such that words which occur fewer than <min_count> times are discarded. Default: 0",
            "type": int,
            "default": 0,
        },
        "symmetric": {
            "help": "If False, only use left context; if True (default), use left and right",
            "type": str_to_bool,
            "default": True,
        },
        "window_size": {
            "help": "Number of context words to the left (and to the right, if symmetric = 1); default 15",
            "type": int,
            "default": 15,
        },
        "memory": {
            "help": "Soft limit for memory consumption, in GB -- based on simple heuristic, so not extremely accurate; "
                    "default 4.0",
            "type": float,
            "default": 4.,
        },
        "max_product": {
            "help": "Limit the size of dense cooccurrence array by specifying the max product of the frequency "
                    "counts of the two cooccurring words. This value overrides that which is automatically "
                    "produced by 'memory'. Typically only needs adjustment for use with very large corpora.",
            "type": int,
        },
        "overflow_length": {
            "help": "Limit to length the sparse overflow array, which buffers cooccurrence data that does not fit in "
                    "the dense array, before writing to disk. This value overrides that which is automatically "
                    "produced by 'memory'. Typically only needs adjustment for use with very large corpora.",
            "type": int,
        },
        "distance_weighting": {
            "help": "If False, do not weight cooccurrence count by distance between words; if True (default), "
                    "weight the cooccurrence count by inverse of distance between words",
            "type": str_to_bool,
            "default": True,
        },
        "array_size": {
            "help": "Limit to length <array_size> the buffer which stores chunks of data to shuffle before writing "
                    "to disk. This value overrides that which is automatically produced by 'memory'",
            "type": int,
        },
        "seed": {
            "help": "Random seed to use for shuffling. If not set, will be randomized using current time",
            "type": int,
        },
        "vector_size": {
            "help": "Dimension of word vector representations (excluding bias term); default 50",
            "type": int,
            "default": 50,
        },
        "threads": {
            "help": "Number of threads during training; default 8",
            "type": int,
            "default": 8,
        },
        "iter": {
            "help": "Number of training iterations; default 25",
            "type": int,
            "default": 25,
        },
        "eta": {
            "help": "Initial learning rate; default 0.05",
            "type": float,
            "default": 0.05,
        },
        "alpha": {
            "help": "Parameter in exponent of weighting function; default 0.75",
            "type": float,
            "default": 0.75,
        },
        "x_max": {
            "help": "Parameter specifying cutoff in weighting function; default 100.0",
            "type": float,
            "default": 100.,
        },
        "grad_clip": {
            "help": "Gradient components clipping parameter. Values will be clipped to [-grad-clip, grad-clip] interval",
            "type": float,
        },
    }
    module_supports_python2 = False

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [glove_dependency, numpy_dependency]
