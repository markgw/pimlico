import os

from pimlico.core.dependencies.python import gensim_dependency
from pimlico.datatypes import PimlicoDatatype


class GensimLdaModel(PimlicoDatatype):
    datatype_name = "lda_model"

    def get_software_dependencies(self):
        return super(GensimLdaModel, self).get_software_dependencies() + [gensim_dependency]

    class Reader:
        def load_model(self):
            from gensim.models.ldamodel import LdaModel
            return LdaModel.load(os.path.join(self.data_dir, "model"))

    class Writer:
        required_tasks = ["model"]

        def write_model(self, model):
            model.save(os.path.join(self.data_dir, "model"))
            self.task_complete("model")
