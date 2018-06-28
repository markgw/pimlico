# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Named-entity recognition using OpenNLP's tools.

By default, uses the pre-trained English model distributed with OpenNLP. If you want to use other models (e.g.
for other languages), download them from the OpenNLP website to the models dir (`models/opennlp`) and specify
the model name as an option.

Note that the default model is for identifying person names only. You can identify other name types by loading
other pre-trained OpenNLP NER models. Identification of multiple name types at the same time is not (yet)
implemented.

"""
import os

from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.old_datatypes.spans import SentenceSpansCorpus, SentenceSpansCorpusWriter
from pimlico.old_datatypes.tar import TarredCorpusType
from pimlico.old_datatypes.tokenized import TokenizedDocumentType
from pimlico.old_datatypes.word_annotations import WordAnnotationsDocumentType
from pimlico.modules.opennlp.deps import py4j_wrapper_dependency


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_ner"
    module_readable_name = "OpenNLP NER"
    module_inputs = [("text", TarredCorpusType(TokenizedDocumentType, WordAnnotationsDocumentType))]
    module_outputs = [("documents", SentenceSpansCorpus)]
    module_options = {
        "model": {
            "help": "NER model, full path or filename. If a filename is given, it is expected to be in the "
                    "opennlp model directory (models/opennlp/)",
            "default": "en-ner-person.bin",
        },
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        self.model_path = abs_path_or_model_dir_path(self.options["model"], "opennlp")

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + dependencies

    def get_writer(self, output_name, output_dir, append=False):
        return SentenceSpansCorpusWriter(output_dir, append=append)

    def check_ready_to_run(self):
        problems = super(ModuleInfo, self).check_ready_to_run()
        # Check models exist
        if not os.path.exists(self.model_path):
            problems.append(("Missing OpenNLP NER model", "Path %s does not exist" % self.model_path))
        return problems


dependencies = [
    py4j_wrapper_dependency("pimlico.opennlp.NERGateway"),
]
