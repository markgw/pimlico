# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
`CAEVO <http://www.usna.edu/Users/cs/nchamber/caevo/>`_ is Nate Chambers' CAscading EVent Ordering system,
a tool for extracting events of many types from text and ordering them.

`CAEVO is open source <https://github.com/nchambers/caevo>`_, implemented in Java, so is easily integrated
into Pimlico using Py4J.

.. todo::

   Replace check_runtime_dependencies() with get_software_dependencies()

"""

import os
from pimlico import MODEL_DIR, JAVA_BUILD_JAR_DIR
from pimlico.core.dependencies.java import argparse4j_dependency
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.caevo import CaevoCorpus
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter
from .deps import caevo_dependency, caevo_wrapper_dependency


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "caevo"
    module_readable_name = "CAEVO event extractor"
    module_inputs = [("documents", TarredCorpus)]
    module_outputs = [("events", CaevoCorpus)]
    module_options = {
        "sieves": {
            "help": "Filename of sieve list file, or path to the file. If just a filename, assumed to be in Caevo "
                    "model dir (models/caevo). Default: default.sieves (supplied with Caevo)",
            "default": "default.sieves",
        },
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        # Postprocess model option
        self.sieves_path = abs_path_or_model_dir_path(self.options["sieves"], "caevo")
        self.wordnet_dir = os.path.join(MODEL_DIR, "caevo", "dict")
        self.template_jwnl_path = os.path.join(JAVA_BUILD_JAR_DIR, "caevo_jwnl_file_properties.xml")

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [
            argparse4j_dependency,
            caevo_wrapper_dependency,
            caevo_dependency
        ]

    def get_writer(self, output_name, output_dir, append=False):
        return TarredCorpusWriter(output_dir, append=append, gzip=True)
