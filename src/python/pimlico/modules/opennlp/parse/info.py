# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
.. todo::

   Document this module

"""
import os
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes.parse import ConstituencyParseTreeCorpus, ConstituencyParseTreeCorpusWriter
from pimlico.datatypes.tokenized import TokenizedCorpus
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, WordAnnotationCorpusWithRequiredFields
from pimlico.modules.opennlp.deps import py4j_wrapper_dependency


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

    def get_writer(self, output_name, output_dir, append=False):
        return ConstituencyParseTreeCorpusWriter(output_dir, append=append)

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
