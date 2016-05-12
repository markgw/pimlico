# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
.. todo::

   Document this module

"""
import os

from pimlico.core.external.java import check_java_dependency, DependencyCheckerError
from pimlico.core.modules.base import DependencyError
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.tokenized import TokenizedCorpus
from pimlico.datatypes.parse import ConstituencyParseTreeCorpus, ConstituencyParseTreeCorpusWriter
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, WordAnnotationCorpusWithRequiredFields


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_parser"
    module_readable_name = "OpenNLP constituency parser"
    module_inputs = [("documents", (TokenizedCorpus, WordAnnotationCorpusWithRequiredFields("word")))]
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
        doc_input = self.get_input("documents")
        if isinstance(doc_input, WordAnnotationCorpus):
            # Input is coming from a word-annotation corpus -- pull out the words
            self._preprocess_doc = self._preprocess_word_annotations
        else:
            # Don't do anything: we've got tokenized text already
            self._preprocess_doc = lambda doc: doc

    def _preprocess_word_annotations(self, doc):
        """
        Pull word fields out of word annotations, so it's just like a tokenized corpus.
        """
        return "\n".join(" ".join(token["word"] for token in sentence) for sentence in doc)

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

    def get_writer(self, output_name, output_dir, append=False):
        return ConstituencyParseTreeCorpusWriter(output_dir, append=append)
