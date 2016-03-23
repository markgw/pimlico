import os

from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus
from .datatypes import PosTaggedCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_pos_tagger"
    module_inputs = [("text", TokenizedCorpus)]
    module_outputs = [("documents", PosTaggedCorpus)]
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

    def check_runtime_dependencies(self):
        missing_dependencies = []

        # We need Py4j to call the tokenizer
        try:
            import py4j
        except ImportError:
            missing_dependencies.append(("Py4J", self.module_name, "Install in lib/python/ dir using 'make py4j'"))

        # Check whether the OpenNLP POS tagger is available
        try:
            class_name = "pimlico.opennlp.PosTaggerGateway"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("OpenNLP POS tagger wrapper",
                                             self.module_name,
                                             "Couldn't load %s. Build the OpenNLP Java wrapper module provided with "
                                             "Pimlico" % class_name))
        except DependencyCheckerError, e:
            missing_dependencies.append(("Java dependency checker", self.module_name, str(e)))

        # Check model files are available
        if not os.path.exists(self.model_path):
            missing_dependencies.append(("OpenNLP POS tagger model", self.module_name,
                                         "Path %s does not exist" % self.model_path))

        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies
