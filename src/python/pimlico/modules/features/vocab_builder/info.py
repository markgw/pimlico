from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.dictionary import Dictionary
from pimlico.datatypes.features import TermFeatureListCorpus


class ModuleInfo(BaseModuleInfo):
    module_type_name = "term_feature_vocab_builder"
    module_inputs = [("term_features", TermFeatureListCorpus)]
    module_outputs = [("term_vocab", Dictionary), ("feature_vocab", Dictionary)]
    module_options = {
        "term_threshold": {
            "help": "Minimum number of occurrences required of a term to be included",
            "type": int,
        },
        "term_max_prop": {
            "help": "Include terms that occur in max this proportion of documents",
            "type": int,
        },
        "term_limit": {
            "help": "Limit vocab size to this number of most common entries (after other filters)",
            "type": int,
        },
        "feature_threshold": {
            "help": "Minimum number of occurrences required of a feature to be included",
            "type": int,
        },
        "feature_max_prop": {
            "help": "Include features that occur in max this proportion of documents",
            "type": int,
        },
        "feature_limit": {
            "help": "Limit vocab size to this number of most common entries (after other filters)",
            "type": int,
        },
    }
