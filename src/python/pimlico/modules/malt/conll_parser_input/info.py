# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Converts word-annotations to CoNLL format, ready for input into the Malt parser.
Annotations must contain words and POS tags. If they contain lemmas, all the better; otherwise the word will
be repeated as the lemma.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.old_datatypes.parse.dependency import CoNLLDependencyParseInputCorpus, CoNLLDependencyParseInputCorpusWriter
from pimlico.old_datatypes.word_annotations import WordAnnotationCorpus, WordAnnotationCorpusWithRequiredFields


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "conll_parser_input"
    module_readable_name = "Annotated text to CoNLL dep parse input converter"
    module_inputs = [("annotations", WordAnnotationCorpusWithRequiredFields(["word", "pos"]))]
    module_outputs = [("conll_data", CoNLLDependencyParseInputCorpus)]
    module_options = {}

    def __init__(self, *args, **kwargs):
        super(ModuleInfo, self).__init__(*args, **kwargs)

    def get_writer(self, output_name, output_dir, append=False):
        return CoNLLDependencyParseInputCorpusWriter(output_dir, append=append)
