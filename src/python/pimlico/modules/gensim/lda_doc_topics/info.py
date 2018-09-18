# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Takes a trained LDA model and produces the topic vector for every document in a corpus.

The corpus is given as integer lists documents, which are the integer IDs of the words
in each sentence of each document. It is assumed that the corpus uses the same vocabulary
to map to integer IDs as the LDA model's training corpus, so no further mapping needs to
be done.

.. todo::

   Add test pipeline and test

"""
from pimlico.core.modules.map import DocumentMapModuleInfo
from pimlico.datatypes import GensimLdaModel, GroupedCorpus
from pimlico.datatypes.corpora.floats import VectorDocumentType
from pimlico.datatypes.corpora.ints import IntegerListsDocumentType


class ModuleInfo(DocumentMapModuleInfo):
    module_type_name = "lda_doc_topics"
    module_readable_name = "LDA document topic analysis"
    module_inputs = [
        ("corpus", GroupedCorpus(IntegerListsDocumentType())),
        ("model", GensimLdaModel())
    ]
    module_outputs = [("vectors", GroupedCorpus(VectorDocumentType()))]
    module_options = {}

    def get_output_writer(self, output_name=None, **kwargs):
        if output_name == "vectors":
            # Set the number of vector dims from the model's number of topics
            kwargs["dimensions"] = self.get_input("model").load_model().num_topics
        return super(ModuleInfo, self).get_output_writer(output_name=output_name, **kwargs)
