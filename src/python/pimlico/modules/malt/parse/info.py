import os

from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.parse.dependency import CoNLLDependencyParseInputCorpus, CoNLLDependencyParseCorpus, \
    CoNLLDependencyParseCorpusWriter


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "malt"
    module_inputs = [("documents", CoNLLDependencyParseInputCorpus)]
    module_outputs = [("parsed", CoNLLDependencyParseCorpus)]
    module_options = {
        "model": {
            "help": "Filename of parsing model, or path to the file. If just a filename, assumed to be Malt models "
                    "dir (models/malt). Default: engmalt.linear-1.7.mco, which can be acquired by 'make malt' in the "
                    "models dir",
            "default": "engmalt.linear-1.7.mco",
        },
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        # Postprocess model option
        self.model_path = abs_path_or_model_dir_path(self.options["model"], "malt")

    def check_runtime_dependencies(self):
        missing_dependencies = []

        # Make sure the model is available
        if not os.path.exists(self.model_path):
            missing_dependencies.append(
                ("Malt parser model", self.module_name, "Parsing model file doesn't exists: %s" % self.model_path)
            )

        # Check whether the OpenNLP POS tagger is available
        try:
            class_name = "pimlico.malt.ParserGateway"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("Malt parser wrapper",
                                             self.module_name,
                                             "Couldn't load %s. Build the Malt Java wrapper module provided with "
                                             "Pimlico ('ant malt')" % class_name))
        except DependencyCheckerError, e:
            missing_dependencies.append(("Java dependency checker", self.module_name, str(e)))

        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies

    def get_writer(self, output_name, append=False):
        return CoNLLDependencyParseCorpusWriter(self.get_output_dir(output_name))
