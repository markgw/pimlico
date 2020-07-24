# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Part-of-speech tagging using OpenNLP's tools.

By default, uses the pre-trained English model distributed with OpenNLP. If you want to use other models (e.g.
for other languages), download them from the OpenNLP website to the models dir (`models/opennlp`) and specify
the model name as an option.

"""
import os

from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType
from pimlico.datatypes.corpora.word_annotations import WordAnnotationsDocumentType
from pimlico.modules.opennlp.deps import py4j_wrapper_dependency


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_pos_tagger"
    module_readable_name = "POS-tagger"
    module_inputs = [("text", GroupedCorpus(TokenizedDocumentType()))]
    module_outputs = [("pos", GroupedCorpus(WordAnnotationsDocumentType("pos")))]
    module_options = {
        "model": {
            "help": "POS tagger model, full path or filename. If a filename is given, it is expected to be in the "
                    "opennlp model directory (models/opennlp/)",
            "default": "en-pos-maxent.bin",
        },
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        self.model_path = abs_path_or_model_dir_path(self.options["model"], "opennlp")

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + dependencies

    def check_ready_to_run(self):
        problems = super(ModuleInfo, self).check_ready_to_run()
        # Check models exist
        if not os.path.exists(self.model_path):
            problems.append(("Missing OpenNLP tagger model", "Path %s does not exist" % self.model_path))
        return problems


dependencies = [
    py4j_wrapper_dependency("pimlico.opennlp.PosTaggerGateway"),
]
