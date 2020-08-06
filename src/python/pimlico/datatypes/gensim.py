from __future__ import absolute_import, print_function

from builtins import object
import os

from pimlico.core.dependencies.python import gensim_dependency
from pimlico.datatypes import PimlicoDatatype

__all__ = ["GensimLdaModel"]


class GensimLdaModel(PimlicoDatatype):
    """
    Storage of trained Gensim LDA models.

    Depends on Gensim (and thereby also in Python 3), since we use Gensim to store and load
    the models.

    """
    datatype_name = "lda_model"
    datatype_supports_python2 = False

    def get_software_dependencies(self):
        return super(GensimLdaModel, self).get_software_dependencies() + [gensim_dependency]

    def run_browser(self, reader, opts):
        """
        Browse the LDA model simply by printing out all its topics.

        """
        model = reader.load_model()
        print("Showing all {} trained LDA topics:".format(model.num_topics))
        for topic, topic_repr in model.show_topics(num_topics=-1, num_words=10):
            print(u"#{}: {}".format(topic, topic_repr).encode("utf-8"))

    class Reader(object):
        def load_model(self):
            from gensim.models.ldamodel import LdaModel
            return LdaModel.load(os.path.join(self.data_dir, "model"))

    class Writer(object):
        required_tasks = ["model"]

        def write_model(self, model):
            model.save(os.path.join(self.data_dir, "model"))
            self.task_complete("model")
