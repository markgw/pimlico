import os

from pimlico import MODEL_DIR
from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.coref.opennlp import CorefCorpus, CorefCorpusWriter
from pimlico.datatypes.parse import ConstituencyParseTreeCorpus


WORDNET_DIR = os.path.join(MODEL_DIR, "wordnet", "db-3.1")


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_coref"
    module_inputs = [("parses", ConstituencyParseTreeCorpus)]
    module_outputs = [("coref", CorefCorpus)]
    module_options = {
        "model": {
            "help": "Coreference resolution model, full path or directory name. If a filename is given, it is expected "
                    "to be in the OpenNLP model directory (models/opennlp/). Default: '' (standard English opennlp model in "
                    "models/opennlp/)",
            "default": "",
        },
        "gzip": {
            "help": "If True, each output, except annotations, for each document is gzipped. This can help reduce the "
                    "storage occupied by e.g. parser or coref output. Default: False",
            "type": str_to_bool,
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
            class_name = "pimlico.opennlp.CoreferenceResolverGateway"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("OpenNLP coref wrapper",
                                             self.module_name,
                                             "Couldn't load %s. Build the OpenNLP Java wrapper module provided with "
                                             "Pimlico" % class_name))
        except DependencyCheckerError, e:
            missing_dependencies.append(("Java dependency checker", self.module_name, str(e)))

        # Check model files are available
        if not os.path.exists(self.model_path):
            missing_dependencies.append(("OpenNLP coref model", self.module_name,
                                         "Path %s does not exist" % self.model_path))

        # For coref, we also need WordNet dictionary files
        if not os.path.exists(WORDNET_DIR):
            missing_dependencies.append(("WordNet dictionaries", self.module_name,
                                         "Download together with OpenNLP coref model using 'make opennlp' in model dir"
                                         ))

        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies

    def get_writer(self, output_name, append=False):
        return CorefCorpusWriter(
            self.get_output_dir(output_name),
            gzip=self.options["gzip"],
            append=append
        )
