import os

from pimlico import JAVA_LIB_DIR
from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus


class ModuleInfo(DocumentMapModuleInfo):
    """
    Incomplete wrapper around the Java C&C parser. Java C&C does not include a supertagger, so we're going to need
    to supply a wrapper around a supertagger before we can use it.

    We need also need to process the output from Java C&C once we're getting it.
    
    """
    module_type_name = "candc"
    module_inputs = [("documents", TokenizedCorpus)]
    # TODO Replace this with a more specific output type
    module_outputs = [("parsed", TarredCorpus)]
    module_options = {
        "model_path": {
            "help": "Filename of parsing model (weights file). Default: model provided with the parser",
            "default": os.path.join(JAVA_LIB_DIR, "candc", "model", "weights"),
        },
        "grammar_dir": {
            "help": "Path to CCG grammar dir. Default: grammar provided with the parser",
            "default": os.path.join(JAVA_LIB_DIR, "candc", "grammar"),
        },
        "lexicon_path": {
            "help": "Path to lexicon file. Default: lexicon file provided with the parser",
            "default": os.path.join(JAVA_LIB_DIR, "candc", "words_feats", "wsj02-21.wordsPos"),
        },
        "features_path": {
            "help": "Path to features file. Default: features file provided with the parser",
            "default": os.path.join(JAVA_LIB_DIR, "candc", "words_feats", "wsj02-21.feats.all.lambda=5"),
        },
        "params_path": {
            "help": "Path to params file to pass into the parser to override default parser settings. "
                    "Default: no params file read, parser uses default setting",
        },
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        # Postprocess model options
        self.model_path = os.path.abspath(self.options["model_path"])
        self.grammar_dir = os.path.abspath(self.options["grammar_dir"])
        self.lexicon_path = os.path.abspath(self.options["lexicon_path"])
        self.features_path = os.path.abspath(self.options["features_path"])
        self.params_path = self.options["params_path"]

    def check_runtime_dependencies(self):
        missing_dependencies = []

        # Make sure the model files are available
        for model_filename in [self.model_path, self.grammar_dir, self.lexicon_path, self.features_path]:
            if not os.path.exists(model_filename):
                missing_dependencies.append(
                    ("C&C model file", self.module_name, "Parsing model file doesn't exist: %s" % model_filename)
                )

        try:
            class_name = "pimlico.candc.CandcGateway"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("C&C parser wrapper",
                                             self.module_name,
                                             "Couldn't load %s. Build the C&C Java wrapper module provided with "
                                             "Pimlico ('ant candc')" % class_name))
        except DependencyCheckerError, e:
            missing_dependencies.append(("Java dependency checker", self.module_name, str(e)))

        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies

    def get_writer(self, output_name, output_dir, append=False):
        return TarredCorpusWriter(output_dir, append=append)
