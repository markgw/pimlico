# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Train fastText embeddings on a tokenized corpus.

Uses the `fastText Python package <https://fasttext.cc/docs/en/python-module.html>`.

FastText embeddings store more than just a vector for each word, since they
also have sub-word representations. We therefore store a standard embeddings
output, with the word vectors in, and also a special fastText embeddings output.

"""
from pimlico.core.dependencies.python import PythonPackageOnPip, numpy_dependency, fasttext_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.core.modules.options import choose_from_list
from pimlico.datatypes import GroupedCorpus, Embeddings
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType
from pimlico.datatypes.embeddings import FastTextEmbeddings


class ModuleInfo(BaseModuleInfo):
    module_type_name = "fasttext"
    module_readable_name = "fastText embedding trainer"
    module_inputs = [("text", GroupedCorpus(TokenizedDocumentType()))]
    module_outputs = [("embeddings", Embeddings()), ("model", FastTextEmbeddings())]
    module_options = {
        "model": {
            "help": "unsupervised fasttext model: cbow, skipgram. Default: skipgram",
            "type": choose_from_list(["skipgram", "cbow"]),
            "default": "skipgram",
        },
        "dim": {
            "help": "size of word vectors. Default: 100",
            "type": int,
            "default": 100,
        },
        "lr": {
            "help": "learning rate. Default: 0.05",
            "type": float,
            "default": 0.05,
        },
        "ws": {
            "help": "size of the context window. Default: 5",
            "type": int,
            "default": 5,
        },
        "epoch": {
            "help": "number of epochs. Default: 5",
            "type": int,
            "default": 5,
        },
        "min_count": {
            "help": "minimal number of word occurences. Default: 5",
            "type": int,
            "default": 5,
        },
        "minn": {
            "help": "min length of char ngram. Default: 3",
            "type": int,
            "default": 3,
        },
        "maxn": {
            "help": "max length of char ngram. Default: 6",
            "type": int,
            "default": 6,
        },
        "neg": {
            "help": "number of negatives sampled. Default: 5",
            "type": int,
            "default": 5,
        },
        "word_ngrams": {
            "help": "max length of word ngram. Default: 1",
            "type": int,
            "default": 1,
        },
        "loss": {
            "help": "loss function: ns, hs, softmax, ova. Default: ns",
            "type": choose_from_list(["ns", "hs", "softmax", "ova"]),
            "default": "ns",
        },
        "bucket": {
            "help": "number of buckets. Default: 2,000,000",
            "type": int,
            "default": 2000000,
        },
        "lr_update_rate": {
            "help": "change the rate of updates for the learning rate. Default: 100",
            "type": int,
            "default": 100,
        },
        "t": {
            "help": "sampling threshold. Default: 0.0001",
            "type": float,
            "default": 0.0001,
        },
        "verbose": {
            "help": "verbose. Default: 2",
            "type": int,
            "default": 2,
        },
    }
    module_supports_python2 = False

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [
            fasttext_dependency, numpy_dependency,
        ]
