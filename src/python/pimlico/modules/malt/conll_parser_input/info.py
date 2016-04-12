from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.parse.dependency import CoNLLDependencyParseInputCorpus, CoNLLDependencyParseInputCorpusWriter
from pimlico.datatypes.word_annotations import WordAnnotationCorpus, WordAnnotationCorpusWithFields


class ModuleInfo(DocumentMapModuleInfo):
    """
    Converts word-annotations to CoNLL format, ready for input into the Malt parser.
    Annotations must contain words and POS tags. If they contain lemmas, all the better; otherwise the word will
    be repeated as the lemma.

    """
    module_type_name = "conll_parser_input"
    module_inputs = [("annotations", WordAnnotationCorpusWithFields(["word", "pos"]))]
    module_outputs = [("conll_data", CoNLLDependencyParseInputCorpus)]
    module_options = {}

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)

    def check_runtime_dependencies(self):
        return []

    def get_writer(self, output_name, append=False):
        return CoNLLDependencyParseInputCorpusWriter(self.get_output_dir(output_name))
