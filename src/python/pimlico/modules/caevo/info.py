# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
`CAEVO <http://www.usna.edu/Users/cs/nchamber/caevo/>`_ is Nate Chambers' CAscading EVent Ordering system,
a tool for extracting events of many types from text and ordering them.

`CAEVO is open source <https://github.com/nchambers/caevo>`_, implemented in Java, so is easily integrated
into Pimlico using Py4J.

"""
import os

from pimlico import MODEL_DIR, JAVA_BUILD_JAR_DIR
from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.caevo import CaevoCorpus
from pimlico.datatypes.tar import TarredCorpus, TarredCorpusWriter


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

    def check_runtime_dependencies(self):
        missing_dependencies = []

        # Make sure the model is available
        if not os.path.exists(self.sieves_path):
            missing_dependencies.append(
                ("Sieve list", self.module_name, "Sieve list file doesn't exists: %s" % self.sieves_path)
            )

        try:
            # Check for Caevo wrapper
            class_name = "pimlico.caevo.CaevoGateway"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("Caevo wrapper", self.module_name, "Couldn't load %s" % class_name))

            # Check for Caevo itself
            class_name = "caevo.SieveDocument"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("Caevo jar",
                                             self.module_name,
                                             "Couldn't load %s. Install Caevo by running 'make caevo' in Java lib dir" %
                                             class_name))

            # Argparse4j
            class_name = "net.sourceforge.argparse4j.ArgumentParsers"
            try:
                check_java_dependency(class_name)
            except DependencyError:
                missing_dependencies.append(("argparse4j",
                                             self.module_name,
                                             "Couldn't load %s. Install argparse4j by running 'make argparse4j' in "
                                             "Java lib dir" % class_name))
        except DependencyCheckerError, e:
            missing_dependencies.append(("Java dependency checker", self.module_name, str(e)))

        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies

    def get_writer(self, output_name, output_dir, append=False):
        return TarredCorpusWriter(output_dir, append=append, gzip=True)
