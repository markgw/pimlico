# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

"""
.. todo::

   Document this module

.. todo::

   Update to new datatypes system and add test pipeline

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import comma_separated_strings, str_to_bool
from pimlico.old_datatypes.features import TermFeatureListCorpus, TermFeatureListCorpusWriter, \
    KeyValueListDocumentType
from pimlico.old_datatypes.tar import TarredCorpusType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "term_feature_list"
    module_readable_name = "Key-value to term-feature converter"
    module_inputs = [("key_values", TarredCorpusType(KeyValueListDocumentType))]
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
    module_supports_python2 = True

    def get_writer(self, output_name, output_dir, append=False):
        return TermFeatureListCorpusWriter(output_dir, append=append)
