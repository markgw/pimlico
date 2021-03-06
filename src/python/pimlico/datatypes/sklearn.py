# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import absolute_import
from builtins import object
from pimlico.core.dependencies.python import sklearn_dependency
from pimlico.datatypes import NamedFile


class SklearnModel(NamedFile):
    """
    Saves and loads scikit-learn models using the library's joblib functions.

    See `the sklearn docs for more details <http://scikit-learn.org/stable/modules/model_persistence.html>`_

    """
    datatype_name = "sklearn_model"
    datatype_supports_python2 = True

    def __init__(self, *args, **kwargs):
        super(SklearnModel, self).__init__("model.pkl", *args, **kwargs)

    def get_software_dependencies(self):
        return super(SklearnModel, self).get_software_dependencies() + [sklearn_dependency]

    class Reader(object):
        def load_model(self):
            import joblib
            return joblib.load(self.get_absolute_path("model.pkl"))

    class Writer(object):
        def save_model(self, model):
            import joblib
            joblib.dump(model, self.get_absolute_path("model.pkl"))
            self.task_complete("write_model.pkl")
