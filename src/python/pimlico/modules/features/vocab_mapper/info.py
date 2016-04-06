from pimlico.core.modules.base import BaseModuleInfo
from pimlico.datatypes.dictionary import Dictionary
from pimlico.datatypes.features import TermFeatureListCorpus, IndexedTermFeatureListCorpus


class ModuleInfo(BaseModuleInfo):
    module_type_name = "term_feature_vocab_mapper"
    module_inputs = [
        ("data", TermFeatureListCorpus), ("term_vocab", Dictionary), ("feature_vocab", Dictionary)
    ]
    module_outputs = [("data", IndexedTermFeatureListCorpus)]
    module_options = {}
