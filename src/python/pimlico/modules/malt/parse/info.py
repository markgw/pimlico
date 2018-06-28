# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
.. todo::

   Document this module

"""
import os

from pimlico.core.dependencies.java import check_java_dependency, PimlicoJavaLibrary, JavaJarsDependency
from pimlico.core.external.java import DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.old_datatypes.parse.dependency import CoNLLDependencyParseCorpus, \
    CoNLLDependencyParseCorpusWriter, CoNLLDependencyParseDocumentType
from pimlico.old_datatypes.tar import TarredCorpusType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "malt"
    module_readable_name = "Malt dependency parser"
    module_inputs = [("documents", TarredCorpusType(CoNLLDependencyParseDocumentType))]
    module_outputs = [("parsed", CoNLLDependencyParseCorpus)]
    module_options = {
        "model": {
            "help": "Filename of parsing model, or path to the file. If just a filename, assumed to be Malt models "
                    "dir (models/malt). Default: engmalt.linear-1.7.mco, which can be acquired by 'make malt' in the "
                    "models dir",
            "default": "engmalt.linear-1.7.mco",
        },
        "no_gzip": {
            "help": "By default, we gzip each document in the output data. If you don't do this, the output can get "
                    "very large, since it's quite a verbose output format",
            "type": str_to_bool,
            "default": False,
        }
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        # Postprocess model option
        self.model_path = abs_path_or_model_dir_path(self.options["model"], "malt")

    def get_software_dependencies(self):
        return [
            PimlicoJavaLibrary("Malt wrapper", classes=["pimlico.malt.ParserGateway"]),
            JavaJarsDependency(
                "liblinear",
                [("liblinear-java-1.95.jar", "http://www.bwaldvogel.de/liblinear-java/liblinear-java-1.95.jar")]
            ),
            JavaJarsDependency(
                "log4j",
                [("log4j-1.2.17.jar", "http://www.us.apache.org/dist/logging/log4j/1.2.17/log4j-1.2.17.tar.gz"
                                      "->apache-log4j-1.2.17/log4j-1.2.17.jar")]
            ),
            JavaJarsDependency(
                "Malt parser",
                [("maltparser-1.8.1.jar", "http://maltparser.org/dist/maltparser-1.8.1.tar.gz"
                                          "->maltparser-1.8.1/maltparser-1.8.1.jar")]
            ),
        ]

    def check_ready_to_run(self):
        problems = super(ModuleInfo, self).check_ready_to_run()
        # Check model exists
        if not os.path.exists(self.model_path):
            problems.append(("Missing Malt parser model", "Path %s does not exist" % self.model_path))
        return problems

    def get_writer(self, output_name, output_dir, append=False):
        return CoNLLDependencyParseCorpusWriter(output_dir, append=append, gzip=not self.options["no_gzip"])
