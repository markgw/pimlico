from __future__ import absolute_import

import os

from pimlico.core.dependencies.python import gensim_dependency
from pimlico.datatypes import PimlicoDatatype, PimlicoDatatypeWriter


class GensimLdaModel(PimlicoDatatype):
    datatype_name = "lda_model"

    def get_software_dependencies(self):
        return super(GensimLdaModel, self).get_software_dependencies() + [gensim_dependency]

    def load_model(self):
        from gensim.models.ldamodel import LdaModel
        return LdaModel.load(os.path.join(self.data_dir, "model"))


class GensimLdaModelWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir):
        super(GensimLdaModelWriter, self).__init__(base_dir)
        self.require_tasks("model")

    def write_model(self, model):
        model.save(os.path.join(self.data_dir, "model"))
        self.task_complete("model")
