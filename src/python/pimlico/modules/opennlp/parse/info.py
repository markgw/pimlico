import os

from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.parse import ConstituencyParseTreeCorpus, ConstituencyParseTreeCorpusWriter
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_parser"
    module_inputs = [("documents", TokenizedCorpus)]
    module_outputs = [("parser", ConstituencyParseTreeCorpus)]
    module_options = {
        "model": {
            "help": "Parser model, full path or directory name. If a filename is given, it is expected "
                    "to be in the OpenNLP model directory (models/opennlp/)",
            "default": "en-parser-chunking.bin",
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
            class_name = "pimlico.opennlp.ParserGateway"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("OpenNLP parser wrapper",
                                             self.module_name,
                                             "Couldn't load %s. Build the OpenNLP Java wrapper module provided with "
                                             "Pimlico" % class_name))
        except DependencyCheckerError, e:
            missing_dependencies.append(("Java dependency checker", self.module_name, str(e)))

        # Check model files are available
        if not os.path.exists(self.model_path):
            missing_dependencies.append(("OpenNLP parsing model", self.module_name,
                                         "Path %s does not exist" % self.model_path))

        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies

    def get_writer(self, output_name, append=False):
        return ConstituencyParseTreeCorpusWriter(
            self.get_output_dir(output_name),
            append=append
        )
