# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Takes a trained LDA model and produces the topic vector for every document in a corpus.

The corpus is given as integer lists documents, which are the integer IDs of the words
in each sentence of each document. It is assumed that the corpus uses the same vocabulary
to map to integer IDs as the LDA model's training corpus, so no further mapping needs to
be done.

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes.floats import VectorDocumentCorpus, VectorDocumentCorpusWriter
from pimlico.datatypes.gensim import GensimLdaModel
from pimlico.datatypes.ints import IntegerListsDocumentType
from pimlico.datatypes.tar import TarredCorpusType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "lda_trainer"
    module_readable_name = "LDA trainer"
    module_inputs = [
        ("corpus", TarredCorpusType(IntegerListsDocumentType)),
        ("model", GensimLdaModel)
    ]
    module_outputs = [("vectors", VectorDocumentCorpus)]
    module_options = {}

    def get_writer(self, output_name, output_dir, append=False):
        num_topics = self.get_input("model").load_model().num_topics
        return VectorDocumentCorpusWriter(self.get_absolute_output_dir("vectors"), num_topics, append=append)
