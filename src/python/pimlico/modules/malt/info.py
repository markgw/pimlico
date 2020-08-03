# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Runs the Malt dependency parser.

Malt is a Java tool, so we use a Py4J wrapper.

Input is supplied as word annotations (which are converted to CoNLL format for
input to the parser). These must include at least each word (field 'word')
and its POS tag (field 'pos'). If a 'lemma' field is supplied, that will
also be used.

The fields in the output contain all of the word features provided by the
parser's output. Some may be ``None`` if they are empty in the parser output.
All the fields in the input (which always include ``word`` and ``pos`` at least)
are also output.

.. todo::

   Update to new datatypes system and add test pipeline.

   Now finished coding, but haven't tested yet.
   - Write a test pipeline
   - Run the OpenNLP POS tagger test pipeline and save the output data (word annotations format)
   - Use this as input to the Malt test pipeline and debug

"""
import os

from pimlico.core.dependencies.java import PimlicoJavaLibrary, JavaJarsDependency
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.word_annotations import WordAnnotationsDocumentType, AddAnnotationFields


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "malt"
    module_readable_name = "Malt dependency parser"
    module_inputs = [("documents", GroupedCorpus(WordAnnotationsDocumentType(["word", "pos"])))]
    module_outputs = [
        ("parsed", AddAnnotationFields("documents", ["feats", "head", "deprel", "phead", "pdeprel"]))
    ]
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

    def get_software_dependencies(self):
        return [
            PimlicoJavaLibrary("malt", classes=["pimlico.malt.ParserGateway"], additional_jars=["argparse4j.jar"]),
            JavaJarsDependency(
                "Malt parser",
                [
                    # All jars are available from the same archive
                    ("maltparser-1.9.2.jar", "http://maltparser.org/dist/maltparser-1.9.2.tar.gz"
                                             "->maltparser-1.9.2/maltparser-1.9.2.jar"),
                    ("liblinear-1.8.jar", "http://maltparser.org/dist/maltparser-1.9.2.tar.gz"
                                          "->maltparser-1.9.2/lib/liblinear-1.8.jar"),
                    ("libsvm.jar", "http://maltparser.org/dist/maltparser-1.9.2.tar.gz"
                                   "->maltparser-1.9.2/lib/libsvm.jar"),
                    ("log4j.jar", "http://maltparser.org/dist/maltparser-1.9.2.tar.gz"
                                  "->maltparser-1.9.2/lib/log4j.jar"),
                ]
            ),
        ]

    def check_ready_to_run(self):
        problems = super(ModuleInfo, self).check_ready_to_run()
        # Check model exists
        if not os.path.exists(self.model_path):
            problems.append(("Missing Malt parser model", "Path %s does not exist" % self.model_path))
        return problems
