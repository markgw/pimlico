from __future__ import absolute_import
from pimlico.core.dependencies.python import sklearn_dependency
from pimlico.datatypes import NamedFile


class SklearnModel(NamedFile):
    """
    Saves and loads scikit-learn models using the library's joblib functions.

    See `the sklearn docs for more details <http://scikit-learn.org/stable/modules/model_persistence.html>`_

    """
    datatype_name = "sklearn_model"

    def __init__(self, *args, **kwargs):
        super(SklearnModel, self).__init__("model.pkl", *args, **kwargs)

    def get_software_dependencies(self):
        return super(SklearnModel, self).get_software_dependencies() + [sklearn_dependency]

    class Reader:
        def load_model(self):
            from sklearn.externals import joblib
            return joblib.load(self.get_absolute_path("model.pkl"))

    class Writer:
        def save_model(self, model):
            from sklearn.externals import joblib
            joblib.dump(model, self.get_absolute_path("model.pkl"))
            self.task_complete("write_model.pkl")
