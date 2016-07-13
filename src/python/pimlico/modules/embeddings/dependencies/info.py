# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
.. todo::

   Document this module

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool, comma_separated_strings
from pimlico.datatypes.features import TermFeatureListCorpus, TermFeatureListCorpusWriter
from pimlico.datatypes.parse.dependency import CoNLLDependencyParseDocumentType
from pimlico.datatypes.tar import TarredCorpusType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "embedding_dep_features"
    module_readable_name = "Dependency feature extractor for embeddings"
    module_inputs = [("dependencies", TarredCorpusType(CoNLLDependencyParseDocumentType))]
    module_outputs = [("term_features", TermFeatureListCorpus)]
    module_options = {
        "lemma": {
            "help": "Use lemmas as terms instead of the word form. Note that if you didn't run a lemmatizer before "
                    "dependency parsing the lemmas are probably actually just copies of the word forms",
            "type": str_to_bool,
        },
        "condense_prep": {
            "help": "Where a word is modified ...TODO"
        },
        "skip_types": {
            "help": "Dependency relations to skip, separated by commas",
            "type": comma_separated_strings,
            "default": [],
        },
        "term_pos": {
            "help": "Only extract features for terms whose POSs are in this comma-separated list. Put a * at the "
                    "end to denote POS prefixes",
            "type": comma_separated_strings,
            "default": [],
        },
    }

    def __init__(self, module_name, pipeline, **kwargs):
        super(ModuleInfo, self).__init__(module_name, pipeline, **kwargs)
        self.include_tags = [pos for pos in self.options["term_pos"] if not pos.endswith("*")]
        self.include_tag_prefixes = [pos[:-1] for pos in self.options["term_pos"] if pos.endswith("*")]
        self.filter_pos = len(self.include_tag_prefixes + self.include_tags) > 0

    def get_writer(self, output_name, output_dir, append=False):
        return TermFeatureListCorpusWriter(output_dir, append=append)
