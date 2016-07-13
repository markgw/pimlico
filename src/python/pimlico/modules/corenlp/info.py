# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Process documents one at a time with the `Stanford CoreNLP toolkit <http://stanfordnlp.github.io/CoreNLP/>`_.
CoreNLP provides a large number of NLP tools, including a POS-tagger, various parsers, named-entity recognition
and coreference resolution. Most of these tools can be run using this module.

The module uses the CoreNLP server to accept many inputs without the overhead of loading models.
If parallelizing, only a single CoreNLP server is run, since this is designed to set multiple Java threads running
if it receives multiple queries at the same time. Multiple Python processes send queries to the server and
process the output.

The module has no non-optional outputs, since what sort of output is available depends on the options you pass in:
that is, on which tools are run. Use the annotations option to choose which word annotations are added.
Otherwise, simply select the outputs that you want and the necessary tools will be run in the CoreNLP pipeline
to produce those outputs.

Currently, the module only accepts tokenized input. If pre-POS-tagged input is given, for example, the POS
tags won't be handed into CoreNLP. In the future, this will be implemented.

We also don't currently provide a way of choosing models other than the standard, pre-trained English models.
This is a small addition that will be implemented in the future.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import choose_from_list, str_to_bool
from pimlico.datatypes.base import DynamicOutputDatatype
from pimlico.datatypes.coref.corenlp import CorefCorpus
from pimlico.datatypes.documents import RawTextDocumentType
from pimlico.datatypes.jsondoc import JsonDocumentCorpus, JsonDocumentCorpusWriter
from pimlico.datatypes.parse import ConstituencyParseTreeCorpus, ConstituencyParseTreeCorpusWriter
from pimlico.datatypes.parse.dependency import StanfordDependencyParseCorpus, StanfordDependencyParseCorpusWriter
from pimlico.datatypes.tar import TarredCorpusType
from pimlico.datatypes.tokenized import TokenizedCorpus, TokenizedCorpusWriter, TokenizedDocumentType
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, SimpleWordAnnotationCorpusWriter, \
    WordAnnotationsDocumentType
from .deps import corenlp_dependencies


class AnnotationFieldsFromOptions(DynamicOutputDatatype):
    def get_datatype(self, module_info):
        from pimlico.core.modules.base import ModuleInfoLoadError

        input_datatype = module_info.get_input_datatype("documents")[1]
        if issubclass(input_datatype, WordAnnotationCorpus):
            if input_datatype.annotation_fields is None:
                raise ModuleInfoLoadError("cannot construct a word annotation corpus type by adding fields to input, "
                                          "since the input type, %s, doesn't explicitly declare its annotation fields" %
                                          input_datatype.__name__)
            base_annotation_fields = input_datatype.annotation_fields
        else:
            # Allow the special case where the input datatype is a tokenized corpus
            # Pretend it's an annotated corpus with no annotations, just words
            base_annotation_fields = []

        # Look at the options to see what annotations are going to be added
        add_fields = module_info.options["annotators"].split(",") if module_info.options["annotators"] else []
        for field in add_fields:
            if field not in ["pos", "ner", "lemma", "word"]:
                raise ModuleInfoLoadError("invalid annotator '%s': choose from pos, ner, lemma" % field)
            if field in base_annotation_fields:
                raise ModuleInfoLoadError("annotation '%s' is already available in the input, but CoreNLP annotator "
                                          "was asked to add it" % field)

        if "word" not in base_annotation_fields + add_fields:
            # Output annotations should always include the word, which is always available
            add_fields.insert(0, "word")

        if issubclass(input_datatype, WordAnnotationCorpus):
            new_datatype_name = "word_annotations_%s" % "+".join(add_fields)
        else:
            new_datatype_name = "%s+%s" % (input_datatype.datatype_name, "+".join(add_fields))

        class ExtendedWordAnnotationCorpus(WordAnnotationCorpus):
            datatype_name = new_datatype_name
            annotation_fields = base_annotation_fields + add_fields

        return ExtendedWordAnnotationCorpus

    def get_base_datatype_class(self):
        return WordAnnotationCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "corenlp"
    module_readable_name = "Stanford CoreNLP"
    module_inputs = [("documents", TarredCorpusType(WordAnnotationsDocumentType,
                                                    TokenizedDocumentType,
                                                    RawTextDocumentType))]
    # No non-optional outputs
    module_outputs = []
    module_optional_outputs = [
        # The default output: annotated words
        ("annotations", AnnotationFieldsFromOptions()),
        # We can also easily get tokenized text from the same source
        ("tokenized", TokenizedCorpus),
        # Constituency parses
        ("parse", ConstituencyParseTreeCorpus),
        # Dependency parses extracted from constituency parses
        ("parse-deps", StanfordDependencyParseCorpus),
        # Dependency parses from dependency parser
        ("dep-parse", StanfordDependencyParseCorpus),
        # Full raw JSON output from the CoreNLP server
        ("raw", JsonDocumentCorpus),
        # Coreference resolution
        ("coref", CorefCorpus),
    ]
    module_options = {
        "annotators": {
            "help": "Comma-separated list of word annotations to add, from CoreNLP's annotators. Choose from: "
                    "word, pos, lemma, ner",
            "default": "",
        },
        "dep_type": {
            "help": "Type of dependency parse to output, when outputting dependency parses, either from a constituency "
                    "parse or direct dependency parse. Choose from the three types allowed by CoreNLP: "
                    "'basic', 'collapsed' or 'collapsed-ccprocessed'",
            "default": "collapsed-ccprocessed",
            "type": choose_from_list(["basic", "collapsed", "collapsed-ccprocessed"]),
        },
        "timeout": {
            "help": "Timeout for the CoreNLP server, which is applied to every job (document). Number of seconds. "
                    "By default, we use the server's default timeout (15 secs), but you may want to increase this "
                    "for more intensive tasks, like coref",
            "type": float,
        },
        "gzip": {
            "help": "If True, each output, except annotations, for each document is gzipped. This can help reduce the "
                    "storage occupied by e.g. parser or coref output. Default: False",
            "type": str_to_bool,
        },
        "readable": {
            "help": "If True, JSON outputs are formatted in a readable fashion, pretty printed. Otherwise, they're "
                    "as compact as possible. Default: False",
            "type": str_to_bool,
        },
        # TODO Add an option to specify model path, for non-standard (e.g. non-English) models
    }

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)
        # Postprocess model options
        #self.sentence_model_path = abs_path_or_model_dir_path(self.options["sentence_model"], "opennlp")
        #self.token_model_path = abs_path_or_model_dir_path(self.options["token_model"], "opennlp")

    def get_software_dependencies(self):
        return super(ModuleInfo, self).get_software_dependencies() + corenlp_dependencies

    def check_ready_to_run(self):
        # TODO Check models are available here, when you've added the model path option
        return super(ModuleInfo, self).check_ready_to_run()

    @staticmethod
    def get_extra_outputs_from_options(options):
        # If the 'annotators' option is given, produce annotations output
        if options["annotators"].strip():
            return ["annotations"]
        else:
            return []

    def get_writer(self, output_name, output_dir, append=False):
        gzip = self.options["gzip"]
        readable = self.options["readable"]
        if output_name == "annotations":
            output_name, output_datatype = self.get_output_datatype(output_name)
            return SimpleWordAnnotationCorpusWriter(output_dir, output_datatype.annotation_fields, append=append)
        elif output_name == "parse":
            # Just write out parse trees as they come from the parser
            return ConstituencyParseTreeCorpusWriter(output_dir, gzip=gzip, append=append)
        elif output_name == "parse-deps":
            return StanfordDependencyParseCorpusWriter(output_dir, gzip=gzip, readable=readable, append=append)
        elif output_name == "dep-parse":
            return StanfordDependencyParseCorpusWriter(output_dir, gzip=gzip, readable=readable, append=append)
        elif output_name == "raw":
            return JsonDocumentCorpusWriter(output_dir, gzip=gzip, readable=readable, append=append)
        elif output_name == "coref":
            return JsonDocumentCorpusWriter(output_dir, gzip=gzip, readable=readable, append=append)
        elif output_name == "tokenized":
            return TokenizedCorpusWriter(output_dir, gzip=gzip, append=append)
        else:
            raise ValueError("unknown output '%s'" % output_name)
