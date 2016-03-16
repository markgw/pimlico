import os
from pimlico import MODEL_DIR
from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.tar import TarredCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_tokenizer"
    module_inputs = [("text", TarredCorpus)]
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
        if not os.path.isabs(self.options["sentence_model"]):
            # Assumed to be in model dir
            self.sentence_model_path = os.path.join(MODEL_DIR, "opennlp", self.options["sentence_model"])
        else:
            self.sentence_model_path = self.options["sentence_model"]

        if not os.path.isabs(self.options["token_model"]):
            self.token_model_path = os.path.join(MODEL_DIR, "opennlp", self.options["token_model"])
        else:
            self.token_model_path = self.options["token_model"]

    def check_runtime_dependencies(self):
        missing_dependencies = []

        # Check whether the OpenNLP tokenizer is available
        try:
            class_name = "opennlp.tools.tokenize.Tokenizer"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("OpenNLP tokenizer", self.module_name,
                                             "Couldn't load %s. Use make to fetch OpenNLP libraries" % class_name))

            # Check our wrapper is available
            class_name = "pimlico.opennlp.Tokenize"
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
