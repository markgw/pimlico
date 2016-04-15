from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.core.modules.options import choose_from_list, str_to_bool
from pimlico.datatypes.coref.corenlp import CorefCorpus
from pimlico.datatypes.jsondoc import JsonDocumentCorpus, JsonDocumentCorpusWriter
from pimlico.datatypes.parse import ConstituencyParseTreeCorpus, ConstituencyParseTreeCorpusWriter
from pimlico.datatypes.parse.dependency import StanfordDependencyParseCorpus, StanfordDependencyParseCorpusWriter
from pimlico.datatypes.tar import TarredCorpus
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, SimpleWordAnnotationCorpusWriter
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus
from .deps import check_corenlp_dependencies


def annotation_fields_from_options(module_info):
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

    class ExtendedWordAnnotationCorpus(WordAnnotationCorpus):
        datatype_name = "%s+%s" % (input_datatype.datatype_name, "+".join(add_fields))
        annotation_fields = base_annotation_fields + add_fields

    return ExtendedWordAnnotationCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "corenlp"
    module_inputs = [("documents", (WordAnnotationCorpus, TokenizedCorpus, TarredCorpus))]
    # No non-optional outputs
    module_outputs = []
    module_optional_outputs = [
        # The default output: annotated words
        ("annotations", annotation_fields_from_options),
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

    def check_runtime_dependencies(self):
        missing_dependencies = check_corenlp_dependencies(self.module_name)
        # TODO Check models are available here, when you've added the model path option
        missing_dependencies.extend(super(ModuleInfo, self).check_runtime_dependencies())
        return missing_dependencies

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
        else:
            raise ValueError("unknown output '%s'" % output_name)
