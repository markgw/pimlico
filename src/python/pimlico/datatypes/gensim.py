# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

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


class GensimLdaSeqModel(PimlicoDatatype):
    """
    A trained LDA-seq model - i.e. Dynamic Topic Model (DTM).

    As well as the Gensim model, it also stores the list of slice labels, so that
    we can easily look up the appropriate time slice for a document paired with
    its slice name. These could be, for example, years or months.

    """
    datatype_name = "ldaseq_model"

    def get_software_dependencies(self):
        return super(GensimLdaSeqModel, self).get_software_dependencies() + [gensim_dependency]

    def run_browser(self, reader, opts):
        """
        Browse the DTM model simply by printing out all its topics.

        """
        model = reader.load_model()
        print("Showing all {} trained DTM topics:".format(model.num_topics))
        for time, label in zip(range(len(model.time_slice)), reader.load_labels()):
            print("Time slice {}".format(time))
            for topic, topic_repr in enumerate(model.print_topics(time=time, top_terms=6)):
                print(u"#{}: {}".format(topic,
                                        ", ".join("{} ({:.3f})".format(word, prob) for (word, prob) in topic_repr)))

    class Reader(object):
        def load_model(self):
            from gensim.models.ldaseqmodel import LdaSeqModel
            return LdaSeqModel.load(os.path.join(self.data_dir, "model"))

        def load_labels(self):
            with open(os.path.join(self.data_dir, "slice_labels.txt"), "r") as f:
                return f.read().splitlines()

    class Writer(object):
        required_tasks = ["model", "slice_labels"]

        def write_model(self, model):
            model.save(os.path.join(self.data_dir, "model"))
            self.task_complete("model")

        def write_labels(self, labels):
            with open(os.path.join(self.data_dir, "slice_labels.txt"), "w") as f:
                f.write("\n".join(labels))
            self.task_complete("slice_labels")
