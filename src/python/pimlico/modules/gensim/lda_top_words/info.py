# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html
"""
Extract the top words for each topic from a Gensim LDA model.

Can be used as input to coherence evaluation.

Currently, this just outputs the highest probability words, but it
could be extended in future to extract words according to other measures,
like `relevance or lift <https://nlp.stanford.edu/events/illvi2014/papers/sievert-illvi2014.pdf>`_.

"""
from pimlico.datatypes.gensim import TopicsTopWords

from pimlico.core.dependencies.python import numpy_dependency, gensim_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import GensimLdaModel


class ModuleInfo(BaseModuleInfo):
    module_type_name = "lda_top_words"
    module_readable_name = "LDA top words"
    module_inputs = [
        ("model", GensimLdaModel()),
    ]
    module_outputs = [("top_words", TopicsTopWords())]
    module_options = {
        "num_words": {
            "help": "Number of words to show per topic. Default: 15",
            "type": int,
            "default": 15,
        },
    }

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [gensim_dependency, numpy_dependency]
