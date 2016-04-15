from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import comma_separated_strings, str_to_bool
from pimlico.datatypes.features import TermFeatureListCorpus, KeyValueListCorpus, TermFeatureListCorpusWriter


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "term_feature_list"
    module_inputs = [("key_values", KeyValueListCorpus)]
    module_outputs = [("term_features", TermFeatureListCorpus)]
    module_options = {
        "term_keys": {
            "help": "Name of keys (feature names in the input) which denote terms. The first one found in the keys "
                    "of a particular data point will be used as the term for that data point. Any other matches will "
                    "be removed before using the remaining keys as the data point's features. Default: just 'term'",
            "type": comma_separated_strings,
            "default": ["term"],
        },
        "include_feature_keys": {
            "help": "If True, include the key together with the value from the input key-value pairs as feature "
                    "names in the output. Otherwise, just use the value. E.g. for input [prop=wordy, poss=my], "
                    "if True we get features [prop_wordy, poss_my] (both with count 1); if False we get just "
                    "[wordy, my]. Default: False",
            "type": str_to_bool,
            "default": False,
        },
    }

    def get_writer(self, output_name, output_dir, append=False):
        return TermFeatureListCorpusWriter(output_dir, append=append)
