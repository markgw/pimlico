# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Constituency parsing using OpenNLP's tools.

We run OpenNLP in the background using a Py4J wrapper, just as with the other
OpenNLP wrappers.

The output format is not yet ideal: currently we produce documents consisting of a
list of strings, each giving the OpenNLP tree output for a sentence. It would be
better to use a standard constituency tree datatype that can be used generically
as input to any modules required tree input. For now, if you write a module taking
input from the parser, it will itself need to process the strings from the OpenNLP
parser output.

"""
import os

from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.parse.trees import OpenNLPTreeStringsDocumentType
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType
from pimlico.modules.opennlp.deps import py4j_wrapper_dependency


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_parser"
    module_readable_name = "Constituency parser"
    module_inputs = [("documents", GroupedCorpus(TokenizedDocumentType()))]
    module_outputs = [("trees", GroupedCorpus(OpenNLPTreeStringsDocumentType()))]
    module_options = {
        "model": {
            "help": "Parser model, full path or directory name. If a filename is given, it is expected "
                    "to be in the OpenNLP model directory (models/opennlp/)",
            "default": "en-parser-chunking.bin",
        },
    }
    module_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        self.model_path = abs_path_or_model_dir_path(self.options["model"], "opennlp")

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + dependencies

    def check_ready_to_run(self):
        problems = super(ModuleInfo, self).check_ready_to_run()
        # Check models exist
        if not os.path.exists(self.model_path):
            problems.append(("Missing OpenNLP parsing model", "Path %s does not exist" % self.model_path))
        return problems


dependencies = [
    py4j_wrapper_dependency("pimlico.opennlp.ParserGateway"),
]
