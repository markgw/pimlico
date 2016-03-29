from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.tar import TarredCorpus
from pimlico.datatypes.word_annotations import WordAnnotationCorpus
from pimlico.modules.opennlp.tokenize.datatypes import TokenizedCorpus
from pimlico.modules.stanford.dependencies import check_corenlp_dependencies


def annotation_fields_from_options(module_info):
    from pimlico.core.modules.base import ModuleInfoLoadError

    # Look at the options to see what annotations are going to be added
    add_fields = module_info.options["annotators"].split(",")
    for field in add_fields:
        if field not in ["pos", "ner", "lemma"]:
            raise ModuleInfoLoadError("invalid annotator '%s': choose from pos, ner, lemma" % field)

    input_datatype = module_info.get_input_datatype("documents")[1]
    # Allow the special case where the input datatype is a tokenized corpus
    # Pretend it's an annotated corpus with no annotations, just words
    if issubclass(input_datatype, (TokenizedCorpus, TarredCorpus)):
        base_annotation_fields = ["word"]
    else:
        if not issubclass(input_datatype, WordAnnotationCorpus):
            raise ModuleInfoLoadError("cannot construct a dynamic word annotation corpus type, since input we're "
                                      "extending isn't a word annotation corpus. Input is a %s" %
                                      input_datatype.__name__)
        if input_datatype.annotation_fields is None:
            raise ModuleInfoLoadError("cannot construct a word annotation corpus type by adding fields to input, "
                                      "since the input type, %s, doesn't explicitly declare its annotation fields" %
                                      input_datatype.__name__)
        base_annotation_fields = input_datatype.annotation_fields

    class ExtendedWordAnnotationCorpus(WordAnnotationCorpus):
        annotation_fields = base_annotation_fields + add_fields

    return ExtendedWordAnnotationCorpus


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "corenlp_annotator"
    module_inputs = [("documents", (WordAnnotationCorpus, TokenizedCorpus, TarredCorpus))]
    module_outputs = [("documents", annotation_fields_from_options)]
    module_options = {
        "annotators": {
            "help": "Comma-separated list of word annotations to add, from CoreNLP's annotators. Choose from: "
                    "pos, lemma, ner",
            "default": "pos",
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
