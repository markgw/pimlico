import os

from pimlico import LIB_DIR
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.parse.candc import CandcOutputCorpusWriter, CandcOutputCorpus
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus


class ModuleInfo(DocumentMapModuleInfo):
    """
    Wrapper around the original C&C parser.
    
    """
    module_type_name = "candc"
    module_inputs = [("documents", TokenizedCorpus)]
    module_outputs = [("parsed", CandcOutputCorpus)]
    module_options = {
        "model": {
            "help": "Absolute path to models directory or name of model set. If not an absolute path, assumed to be "
                    "a subdirectory of the candcs models dir (see instructions in models/candc/README on how to fetch "
                    "pre-trained models)",
            "default": "ccgbank",
        },
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        self.model_path = abs_path_or_model_dir_path(self.options["model"], "candc")
        binary_dir = os.path.join(LIB_DIR, "bin", "candc")
        self.server_binary = os.path.join(binary_dir, "soap_server")
        self.client_binary = os.path.join(binary_dir, "soap_client")

    def check_runtime_dependencies(self):
        missing_dependencies = []

        # Check the parser binaries are available
        for binary_path in [self.server_binary, self.client_binary]:
            if not os.path.exists(binary_path):
                missing_dependencies.append(("C&C parser", self.module_name,
                                             "C&C parser binary %s not available. See lib/bin/README_CANDC for "
                                             "instructions on installing the parser" % binary_path))

        # Make sure the model files are available
        if not os.path.exists(self.model_path):
            missing_dependencies.append(
                ("C&C model dir", self.module_name, "Parsing model directory doesn't exist: %s" % self.model_path)
            )

        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies

    def get_writer(self, output_name, output_dir, append=False):
        return CandcOutputCorpusWriter(output_dir, append=append)
