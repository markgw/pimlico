# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Datatypes for storing and loading Scikit-learn models.

"""
from __future__ import absolute_import

import os

from pimlico.core.dependencies.python import PythonPackageOnPip, sklearn_dependency
from pimlico.datatypes.base import PimlicoDatatypeWriter, PimlicoDatatype


class SklearnModelWriter(PimlicoDatatypeWriter):
    def __init__(self, base_dir, **kwargs):
        super(SklearnModelWriter, self).__init__(base_dir, **kwargs)
        self.require_tasks("model")
        self.model_filename = os.path.join(self.data_dir, "model.pkl")

    def write_model(self, model):
        import joblib
        joblib.dump(model, self.model_filename, protocol=-1, compress=True)
        self.task_complete("model")


class SklearnModel(PimlicoDatatype):
    """
    Datatype for storing Scikit-learn models.

    Very simple storage mechanism: we just pickle the model to a file. Instead of the standard Python pickle
    package, we use `Joblib <https://pythonhosted.org/joblib/>`_, which stores large data objects (especially
    Numpy arrays) more efficiently.

    """
    def __init__(self, base_dir, pipeline, **kwargs):
        super(SklearnModel, self).__init__(base_dir, pipeline, **kwargs)
        self.model_filename = os.path.join(self.data_dir, "model.pkl") if self.data_dir else None

    def get_software_dependencies(self):
        return super(SklearnModel, self).get_software_dependencies() + \
               [sklearn_dependency, PythonPackageOnPip("joblib")]

    def load_model(self):
        import joblib
        return joblib.load(self.model_filename)
