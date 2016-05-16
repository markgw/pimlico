# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
.. todo::

   Document this module

"""
import os

from pimlico.core.external.java import DependencyCheckerError
from pimlico.core.dependencies.java import check_java_dependency
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.tokenized import TokenizedCorpus
from pimlico.datatypes.tar import TarredCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_tokenizer"
    module_readable_name = "OpenNLP tokenizer"
    module_inputs = [("text", TarredCorpus)]
    module_outputs = [("documents", TokenizedCorpus)]
    module_options = {
        "sentence_model": {
            "help": "Sentence segmentation model. Specify a full path, or just a filename. If a filename is given "
                    "it is expected to be in the opennlp model directory (models/opennlp/)",
            "default": "en-sent.bin",
        },
        "token_model": {
            "help": "Tokenization model. Specify a full path, or just a filename. If a filename is given "
                    "it is expected to be in the opennlp model directory (models/opennlp/)",
            "default": "en-token.bin",
        }
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        # Postprocess model options
        self.sentence_model_path = abs_path_or_model_dir_path(self.options["sentence_model"], "opennlp")
        self.token_model_path = abs_path_or_model_dir_path(self.options["token_model"], "opennlp")

    def check_runtime_dependencies(self):
        missing_dependencies = []

        # We need Py4j to call the tokenizer
        try:
            import py4j
        except ImportError:
            missing_dependencies.append(("Py4J", self.module_name, "Install in lib/python/ dir using 'make py4j'"))

        # Check whether the OpenNLP tokenizer is available
        try:
            class_name = "pimlico.opennlp.TokenizerGateway"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("OpenNLP tokenizer wrapper",
                                             self.module_name,
                                             "Couldn't load %s. Build the OpenNLP Java wrapper module provided with "
                                             "Pimlico" % class_name))
        except DependencyCheckerError, e:
            missing_dependencies.append(("Java dependency checker", self.module_name, str(e)))

        # Check model files are available
        if not os.path.exists(self.sentence_model_path):
            missing_dependencies.append(("OpenNLP sentence model", self.module_name,
                                         "Path %s does not exist" % self.sentence_model_path))
        if not os.path.exists(self.token_model_path):
            missing_dependencies.append(("OpenNLP tokenization model", self.module_name,
                                         "Path %s does not exist" % self.token_model_path))

        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies
