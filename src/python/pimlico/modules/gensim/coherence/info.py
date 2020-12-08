"""
Compute topic coherence.

Takes input as a list of the top words for each topic. This can be produced
from various types of topic model, so they can all be evaluated using this method.

Also requires a corpus from which to compute the PMI statistics. This should
typically be a different corpus to that on which the model was trained.

For now, this just computes statistics and outputs them to a text file, and
also outputs a single number representing the mean topic coherence across
topics.

"""
from pimlico.core.modules.options import choose_from_list

from pimlico.datatypes.gensim import TopicsTopWords

from pimlico.core.dependencies.python import gensim_dependency
from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes import GroupedCorpus, NamedFile, Dictionary, NumericResult
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType


class ModuleInfo(BaseModuleInfo):
    module_type_name = "topic_coherence"
    module_readable_name = "Topic model topic coherence"
    module_inputs = [
        ("topics_top_words", TopicsTopWords()),
        ("corpus", GroupedCorpus(TokenizedDocumentType())),
        ("vocab", Dictionary()),
    ]
    module_outputs = [
        ("output", NamedFile("coherence.txt")),
        ("mean_coherence", NumericResult())
    ]
    module_options = {
        "coherence": {
            "help": "Coherence measure to use, selecting from one of Gensim's pre-defined "
                    "measures: 'u_mass', 'c_v', 'c_uci', 'c_npmi'. Default: 'u_mass'",
            "default": "u_mass",
            "type": choose_from_list(['u_mass', 'c_v', 'c_uci', 'c_npmi']),
        },
        "window_size": {
            "help": "Size of the window to be used for coherence measures using boolean sliding window as their "
                    "probability estimator. For ‘u_mass’ this doesn’t matter. "
                    "If None, the default window sizes are used which are: ‘c_v’ - 110, ‘c_uci’ - 10, ‘c_npmi’ - 10.",
            "type": int,
        },
    }

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [gensim_dependency]
