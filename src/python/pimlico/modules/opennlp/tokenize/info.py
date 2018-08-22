# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Sentence splitting and tokenization using OpenNLP's tools.

Sentence splitting may be skipped by setting the option `tokenize_only=T`. The tokenizer
will then assume that each line in the input file represents a sentence and tokenize
within the lines.

.. todo:

   The OpenNLP tokenizer test pipeline needs models to have been installed before running.
   Once `automatic fetching of models/data <https://github.com/markgw/pimlico/issues/9>`_
   has been implemented, use this for the models and move the test pipeline to the main suite.

"""
import os

from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.datatypes import GroupedCorpus
from pimlico.datatypes.corpora.data_points import TextDocumentType
from pimlico.datatypes.corpora.tokenized import TokenizedDocumentType
from pimlico.modules.opennlp.deps import py4j_wrapper_dependency


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "opennlp_tokenizer"
    module_readable_name = "OpenNLP tokenizer"
    module_inputs = [("text", GroupedCorpus(TextDocumentType()))]
    module_outputs = [("documents", GroupedCorpus(TokenizedDocumentType()))]
    module_options = {
        "tokenize_only": {
            "help": "By default, sentence splitting is performed prior to tokenization. If tokenize_only is set, only "
                    "the tokenization step is executed",
            "type": str_to_bool,
            "default": False,
        },
        "sentence_model": {
            "help": "Sentence segmentation model. Specify a full path, or just a filename. If a filename is given "
                    "it is expected to be in the opennlp model directory (models/opennlp/)",
            "default": "en-sent.bin",
        },
        "token_model": {
            "help": "Tokenization model. Specify a full path, or just a filename. If a filename is given "
                    "it is expected to be in the opennlp model directory (models/opennlp/)",
            "default": "en-token.bin",
        }
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        # Postprocess model options
        self.sentence_model_path = abs_path_or_model_dir_path(self.options["sentence_model"], "opennlp")
        self.token_model_path = abs_path_or_model_dir_path(self.options["token_model"], "opennlp")

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + [
            py4j_wrapper_dependency("pimlico.opennlp.TokenizerGateway"),
        ]

    def check_ready_to_run(self):
        problems = super(ModuleInfo, self).check_ready_to_run()
        # Check models exist
        if not self.options["tokenize_only"] and not os.path.exists(self.sentence_model_path):
            problems.append(("Missing OpenNLP sentence model", "Path %s does not exist" % self.sentence_model_path))
        if not os.path.exists(self.token_model_path):
            problems.append(("Missing OpenNLP tokenization model", "Path %s does not exist" % self.token_model_path))
        return problems
