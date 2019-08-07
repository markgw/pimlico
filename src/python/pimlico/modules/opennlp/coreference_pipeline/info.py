# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Runs the full coreference resolution pipeline using OpenNLP. This includes sentence splitting, tokenization,
pos tagging, parsing and coreference resolution. The results of all the stages are available in the output.

.. todo::

   Update to new datatypes system and add test pipeline

"""
from __future__ import division
from past.utils import old_div
import os

from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import str_to_bool
from pimlico.core.paths import abs_path_or_model_dir_path
from pimlico.old_datatypes.coref.opennlp import CorefCorpus, CorefCorpusWriter
from pimlico.old_datatypes.documents import RawTextDocumentType
from pimlico.old_datatypes.parse import ConstituencyParseTreeCorpus, ConstituencyParseTreeCorpusWriter
from pimlico.old_datatypes.tar import TarredCorpusType
from pimlico.old_datatypes.tokenized import TokenizedCorpus, TokenizedCorpusWriter
from pimlico.old_datatypes.word_annotations import WordAnnotationCorpusWithFields, SimpleWordAnnotationCorpusWriter
from pimlico.modules.opennlp.coreference.info import WORDNET_DIR
from pimlico.modules.opennlp.deps import py4j_wrapper_dependency


class ModuleInfo(DocumentMapModuleInfo):
    """
    Use local config setting opennlp_memory to set the limit on Java heap memory for the OpenNLP processes. If
    parallelizing, this limit is shared between the processes. That is, each OpenNLP worker will have a memory
    limit of `opennlp_memory / processes`. That setting can use `g`, `G`, `m`, `M`, `k` and `K`, as in the Java setting.

    """
    module_type_name = "opennlp_coref"
    module_readable_name = "OpenNLP coreference resolution"
    module_inputs = [("text", TarredCorpusType(RawTextDocumentType))]
    module_outputs = [("coref", CorefCorpus)]
    module_optional_outputs = [
        ("tokenized", TokenizedCorpus),
        ("pos", WordAnnotationCorpusWithFields("pos")),
        ("parse", ConstituencyParseTreeCorpus),
    ]
    module_options = {
        "sentence_model": {
            "help": "Sentence segmentation model. Specify a full path, or just a filename. If a filename is given "
                    "it is expected to be in the opennlp model directory (models/opennlp/)",
            "default": "en-sent.bin",
        },
        "token_model": {
            "help": "Tokenization model. Specify a full path, or just a filename. If a filename is given "
                    "it is expected to be in the opennlp model directory (models/opennlp/)",
            "default": "en-token.bin",
        },
        "pos_model": {
            "help": "POS tagger model, full path or filename. If a filename is given, it is expected to be in the "
                    "opennlp model directory (models/opennlp/)",
            "default": "en-pos-maxent.bin",
        },
        "parse_model": {
            "help": "Parser model, full path or directory name. If a filename is given, it is expected "
                    "to be in the OpenNLP model directory (models/opennlp/)",
            "default": "en-parser-chunking.bin",
        },
        "coref_model": {
            "help": "Coreference resolution model, full path or directory name. If a filename is given, it is expected "
                    "to be in the OpenNLP model directory (models/opennlp/). Default: '' (standard English opennlp model in "
                    "models/opennlp/)",
            "default": "",
        },
        "gzip": {
            "help": "If True, each output, except annotations, for each document is gzipped. This can help reduce the "
                    "storage occupied by e.g. parser or coref output. Default: False",
            "type": str_to_bool,
        },
        "readable": {
            "help": "If True, pretty-print the JSON output, so it's human-readable. Default: False",
            "type": str_to_bool,
        },
        "timeout": {
            "help": "Timeout in seconds for each individual coref resolution task. If this is exceeded, an "
                    "InvalidDocument is returned for that document",
            "type": int,
        }
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        self.sentence_model_path = abs_path_or_model_dir_path(self.options["sentence_model"], "opennlp")
        self.token_model_path = abs_path_or_model_dir_path(self.options["token_model"], "opennlp")
        self.pos_model_path = abs_path_or_model_dir_path(self.options["pos_model"], "opennlp")
        self.parse_model_path = abs_path_or_model_dir_path(self.options["parse_model"], "opennlp")
        self.coref_model_path = abs_path_or_model_dir_path(self.options["coref_model"], "opennlp")

    def get_writer(self, output_name, output_dir, append=False):
        if output_name == "coref":
            return CorefCorpusWriter(output_dir,
                                     gzip=self.options["gzip"], readable=self.options["readable"], append=append)
        elif output_name == "tokenized":
            return TokenizedCorpusWriter(output_dir, gzip=self.options["gzip"], append=append)
        elif output_name == "pos":
            return SimpleWordAnnotationCorpusWriter(output_dir, ["word", "pos"],
                                                    gzip=self.options["gzip"], append=append)
        elif output_name == "parse":
            return ConstituencyParseTreeCorpusWriter(output_dir, gzip=self.options["gzip"], append=append)

    def get_heap_memory_limit(self):
        """
        Read in the local config setting opennlp_memory to compute the memory limit per process for Java
        processes.

        """
        # Read in the local config setting
        limit_string = self.pipeline.local_config.get("opennlp_memory", "5G").upper()
        # Get the limit in bytes
        if limit_string.endswith("K"):
            limit = int(limit_string[:-1]) * 1e3
        elif limit_string.endswith("M"):
            limit = int(limit_string[:-1]) * 1e6
        elif limit_string.endswith("G"):
            limit = int(limit_string[:-1]) * 1e9
        else:
            limit = int(limit_string)
        # Divide the allowed memory between the processes
        process_limit = limit // self.pipeline.processes
        # Convert back to a string for the Java option
        # Use units, so debugging output is clearer if we ever need to output the java command
        if process_limit >= 1e10:
            # If the memory per process is over 10G, we can happily round to the nearest G
            process_limit_string = "%dG" % process_limit // 1e9
        elif process_limit >= 1e7:
            process_limit_string = "%dM" % process_limit // 1e6
        elif process_limit >= 1e4:
            process_limit_string = "%dK" % process_limit // 1e3
        else:
            # Just put the whole number
            process_limit_string = "%d" % process_limit
        return process_limit_string

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + dependencies

    def check_ready_to_run(self):
        problems = super(ModuleInfo, self).check_ready_to_run()
        # Check models exist
        if not os.path.exists(self.coref_model_path):
            problems.append(("Missing OpenNLP coref model", "Path %s does not exist" % self.coref_model_path))
        # For coref, we also need WordNet dictionary files
        if not os.path.exists(WORDNET_DIR):
            problems.append(("WordNet dictionaries",
                             "Download together with OpenNLP coref model using 'make opennlp' in model dir"))
        return problems


dependencies = [
    py4j_wrapper_dependency("pimlico.opennlp.CoreferenceResolverRawTextGateway"),
]
